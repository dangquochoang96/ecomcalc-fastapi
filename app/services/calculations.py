from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.calculations import FeeCalculation, ProductCalculation
from app.models.categories import CategoryFee
from app.models.platform_fees import Platform, PlatformFee
from app.models.products import Product
from app.models.user import User
from app.models.user_platform import UserPlatform
from app.schemas.calculations import CalculationCreateRequest

TWOPLACES = Decimal("0.01")
HUNDRED = Decimal("100")
FIXED_FEE_TYPE = 2


class CalculationService:
    @staticmethod
    def create_calculation(
        db: Session, payload: CalculationCreateRequest, current_user: User
    ) -> dict[str, Any]:
        if not payload.products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Products list must not be empty",
            )

        product_ids = [item.product_id for item in payload.products]
        if len(set(product_ids)) != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate product_id found in products list",
            )

        fee_ids = [fee.fee_id for fee in payload.fee_config]
        if len(set(fee_ids)) != len(fee_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate fee_id found in fee_config list",
            )

        platform = (
            db.query(Platform)
            .join(UserPlatform, UserPlatform.platform_id == Platform.id)
            .filter(
                Platform.id == payload.platform_id,
                Platform.is_active.is_(True),
                UserPlatform.user_id == current_user.id,
            )
            .first()
        )
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform not found for current user",
            )

        products = (
            db.query(Product)
            .options(joinedload(Product.category))
            .filter(
                Product.user_id == current_user.id,
                Product.id.in_(product_ids),
                Product.is_active.is_(True),
            )
            .all()
        )
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more products were not found",
            )

        product_map = {product.id: product for product in products}
        platform_fee_map: dict[int, PlatformFee] = {}
        category_fee_map: dict[tuple[int, int], CategoryFee] = {}

        if fee_ids:
            platform_fees = (
                db.query(PlatformFee)
                .filter(
                    PlatformFee.platform_id == payload.platform_id,
                    PlatformFee.id.in_(fee_ids),
                    PlatformFee.is_active.is_(True),
                )
                .all()
            )
            platform_fee_map = {fee.id: fee for fee in platform_fees}
            missing_fee_ids = sorted(set(fee_ids) - set(platform_fee_map.keys()))
            if missing_fee_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid fee ids for platform: {missing_fee_ids}",
                )

            category_ids = [product.category_id for product in products if product.category_id]
            if category_ids:
                category_fees = (
                    db.query(CategoryFee)
                    .filter(
                        CategoryFee.platform_fee_id.in_(fee_ids),
                        CategoryFee.category_id.in_(category_ids),
                    )
                    .all()
                )
                category_fee_map = {
                    (fee.platform_fee_id, fee.category_id): fee for fee in category_fees
                }

        fee_config_payload = []
        for fee in payload.fee_config:
            platform_fee = platform_fee_map.get(fee.fee_id)
            fee_config_payload.append(
                {
                    "fee_id": fee.fee_id,
                    "fee_type": platform_fee.fee_type if platform_fee else None,
                    "custom_value": CalculationService._decimal_to_float(fee.custom_value),
                    "min_value": CalculationService._decimal_to_float(
                        CalculationService._normalize_bound(
                            fee.min_value if fee.min_value is not None else getattr(platform_fee, "min_value", None)
                        )
                    ),
                    "max_value": CalculationService._decimal_to_float(
                        CalculationService._normalize_bound(
                            fee.max_value if fee.max_value is not None else getattr(platform_fee, "max_value", None)
                        )
                    ),
                }
            )

        calculation = FeeCalculation(
            user_id=current_user.id,
            platform_id=payload.platform_id,
            calculation_name=payload.calculation_name,
            notes=payload.notes,
            fee_config=fee_config_payload,
        )
        db.add(calculation)
        db.flush()

        total_revenue = Decimal("0")
        total_fees = Decimal("0")
        total_profit = Decimal("0")
        total_margin = Decimal("0")
        product_calculations = []

        for item in payload.products:
            product = product_map[item.product_id]
            selling_price = CalculationService._to_decimal(item.selling_price)
            cost_price = CalculationService._to_decimal(product.cost_price)
            breakdown = {}
            product_total_fees = Decimal("0")

            for fee in payload.fee_config:
                platform_fee = platform_fee_map.get(fee.fee_id)
                category_fee = category_fee_map.get((fee.fee_id, product.category_id))
                fee_value, rate_value, breakdown_type, applied_min, applied_max = CalculationService._resolve_fee_value(
                    selling_price=selling_price,
                    fee_config=fee,
                    platform_fee=platform_fee,
                    category_fee=category_fee,
                )
                fee_key = CalculationService._resolve_fee_key(
                    fee_name=getattr(platform_fee, "fee_name", None),
                    fee_code=getattr(platform_fee, "fee_code", None),
                    fee_id=fee.fee_id,
                )
                breakdown[fee_key] = {
                    "name": getattr(platform_fee, "fee_name", fee_key),
                    "value": CalculationService._decimal_to_float(fee_value),
                    "type": breakdown_type,
                }
                if rate_value is not None:
                    breakdown[fee_key]["rate"] = CalculationService._decimal_to_float(rate_value)
                if category_fee and product.category:
                    breakdown[fee_key]["category"] = product.category.category_name
                if applied_min is not None:
                    breakdown[fee_key]["min_value"] = CalculationService._decimal_to_float(applied_min)
                if applied_max is not None:
                    breakdown[fee_key]["max_value"] = CalculationService._decimal_to_float(applied_max)

                product_total_fees += fee_value

            revenue = selling_price
            net_profit = revenue - cost_price - product_total_fees
            profit_margin = (
                (net_profit / revenue) * HUNDRED if revenue > 0 else Decimal("0")
            )

            total_revenue += revenue
            total_fees += product_total_fees
            total_profit += net_profit
            total_margin += profit_margin

            product_calculations.append(
                ProductCalculation(
                    fee_calculation_id=calculation.id,
                    product_id=product.id,
                    cost_price=CalculationService._to_decimal(cost_price),
                    selling_price=CalculationService._to_decimal(selling_price),
                    total_fees=CalculationService._to_decimal(product_total_fees),
                    net_profit=CalculationService._to_decimal(net_profit),
                    profit_margin=CalculationService._to_decimal(profit_margin),
                    revenue=CalculationService._to_decimal(revenue),
                    fee_breakdown=breakdown,
                )
            )

        avg_profit_margin = (
            total_margin / Decimal(len(payload.products))
            if payload.products
            else Decimal("0")
        )

        calculation.total_products = len(payload.products)
        calculation.total_revenue = CalculationService._to_decimal(total_revenue)
        calculation.total_fees = CalculationService._to_decimal(total_fees)
        calculation.total_profit = CalculationService._to_decimal(total_profit)
        calculation.avg_profit_margin = CalculationService._to_decimal(avg_profit_margin)

        db.add_all(product_calculations)
        db.commit()
        db.refresh(calculation)

        return {
            "success": True,
            "message": "Tinh toan thanh cong",
            "data": {
                "calculation_id": calculation.id,
                "summary": {
                    "total_products": calculation.total_products,
                    "total_revenue": CalculationService._to_decimal(calculation.total_revenue),
                    "total_fees": CalculationService._to_decimal(calculation.total_fees),
                    "total_profit": CalculationService._to_decimal(calculation.total_profit),
                    "avg_profit_margin": CalculationService._to_decimal(calculation.avg_profit_margin),
                },
            },
        }

    @staticmethod
    def get_calculation_detail(
        db: Session, calculation_id: int, current_user: User
    ) -> dict[str, Any]:
        calculation = (
            db.query(FeeCalculation)
            .options(
                joinedload(FeeCalculation.platform),
                joinedload(FeeCalculation.product_calculations)
                .joinedload(ProductCalculation.product)
                .joinedload(Product.category),
            )
            .filter(
                FeeCalculation.id == calculation_id,
                FeeCalculation.user_id == current_user.id,
            )
            .first()
        )
        if not calculation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calculation not found",
            )

        fee_config = calculation.fee_config or []
        fee_id_list = [fee["fee_id"] for fee in fee_config if fee.get("fee_id") is not None]
        platform_fee_map = {}
        if fee_id_list:
            platform_fees = db.query(PlatformFee).filter(PlatformFee.id.in_(fee_id_list)).all()
            platform_fee_map = {fee.id: fee for fee in platform_fees}

        total_cost = Decimal("0")
        profitable_products = 0
        loss_products = 0
        product_items = []

        for item in calculation.product_calculations:
            cost_price = CalculationService._to_decimal(item.cost_price)
            selling_price = CalculationService._to_decimal(item.selling_price)
            total_fees = CalculationService._to_decimal(item.total_fees)
            net_profit = CalculationService._to_decimal(item.net_profit)
            profit_margin = CalculationService._to_decimal(item.profit_margin)

            total_cost += cost_price
            if net_profit > 0:
                status_value = "profit"
                profitable_products += 1
            elif net_profit < 0:
                status_value = "loss"
                loss_products += 1
            else:
                status_value = "break_even"

            product_items.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.product_name,
                    "sku": item.product.sku,
                    "category_name": item.product.category.category_name
                    if item.product.category
                    else None,
                    "cost_price": cost_price,
                    "selling_price": selling_price,
                    "total_fees": total_fees,
                    "net_profit": net_profit,
                    "profit_margin": profit_margin,
                    "status": status_value,
                    "fee_breakdown": item.fee_breakdown or {},
                }
            )

        fees_applied = []
        for fee in fee_config:
            platform_fee = platform_fee_map.get(fee["fee_id"])
            fees_applied.append(
                {
                    "fee_id": fee["fee_id"],
                    "fee_name": getattr(platform_fee, "fee_name", f"Fee {fee['fee_id']}"),
                    "fee_type": fee.get("fee_type") or getattr(platform_fee, "fee_type", None),
                    "custom_value": CalculationService._nullable_decimal(fee.get("custom_value")),
                    "min_value": CalculationService._nullable_decimal(fee.get("min_value")),
                    "max_value": CalculationService._nullable_decimal(fee.get("max_value")),
                }
            )

        return {
            "success": True,
            "data": {
                "calculation": {
                    "id": calculation.id,
                    "calculation_name": calculation.calculation_name,
                    "calculation_date": calculation.calculation_date,
                    "notes": calculation.notes,
                    "platform": {
                        "id": calculation.platform.id,
                        "name": calculation.platform.name,
                        "code": calculation.platform.code,
                    },
                    "fees_applied": fees_applied,
                },
                "summary": {
                    "total_products": calculation.total_products,
                    "total_revenue": CalculationService._to_decimal(calculation.total_revenue),
                    "total_cost": CalculationService._to_decimal(total_cost),
                    "total_fees": CalculationService._to_decimal(calculation.total_fees),
                    "total_profit": CalculationService._to_decimal(calculation.total_profit),
                    "avg_profit_margin": CalculationService._to_decimal(calculation.avg_profit_margin),
                    "profitable_products": profitable_products,
                    "loss_products": loss_products,
                },
                "products": product_items,
            },
        }

    @staticmethod
    def _resolve_fee_value(
        *,
        selling_price: Decimal,
        fee_config: Any,
        platform_fee: PlatformFee | None,
        category_fee: CategoryFee | None,
    ) -> tuple[Decimal, Decimal | None, str, Decimal | None, Decimal | None]:
        base_value = fee_config.custom_value
        breakdown_type = "custom" if fee_config.custom_value is not None else "default"

        if category_fee is not None:
            base_value = category_fee.fee_value
            breakdown_type = "category_based"
        elif base_value is None and platform_fee is not None:
            base_value = platform_fee.default_value

        min_value = CalculationService._normalize_bound(
            fee_config.min_value if fee_config.min_value is not None else getattr(platform_fee, "min_value", None)
        )
        max_value = CalculationService._normalize_bound(
            fee_config.max_value if fee_config.max_value is not None else getattr(platform_fee, "max_value", None)
        )

        amount = Decimal("0")
        rate_value = None
        if base_value is not None:
            base_value = CalculationService._apply_value_bounds(
                value=CalculationService._to_decimal(base_value),
                min_value=min_value,
                max_value=max_value,
            )
            if platform_fee and platform_fee.fee_type == FIXED_FEE_TYPE:
                amount = base_value
                if breakdown_type == "default":
                    breakdown_type = "fixed"
            else:
                rate_value = base_value
                amount = (selling_price * base_value) / HUNDRED
                if breakdown_type == "default":
                    breakdown_type = "percent"

        return (
            CalculationService._to_decimal(amount),
            CalculationService._nullable_decimal(rate_value),
            breakdown_type,
            min_value,
            max_value,
        )

    @staticmethod
    def _apply_value_bounds(
        *,
        value: Decimal,
        min_value: Decimal | None,
        max_value: Decimal | None,
    ) -> Decimal:
        result = CalculationService._to_decimal(value)
        if min_value is not None:
            result = max(result, min_value)
        if max_value is not None:
            result = min(result, max_value)
        return CalculationService._to_decimal(result)

    @staticmethod
    def _normalize_bound(value: Any) -> Decimal | None:
        if value is None:
            return None
        normalized = CalculationService._to_decimal(value)
        if normalized <= Decimal("0"):
            return None
        return normalized

    @staticmethod
    def _resolve_fee_key(fee_name: str | None, fee_code: str | None, fee_id: int) -> str:
        raw_value = f"{fee_name or ''} {fee_code or ''}".lower()
        if "commission" in raw_value or "hoa hong" in raw_value:
            return "commission"
        if "shipping" in raw_value or "van chuyen" in raw_value:
            return "shipping"
        if "payment" in raw_value or "thanh toan" in raw_value:
            return "payment"
        return fee_code.lower() if fee_code else f"fee_{fee_id}"

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if value is None:
            value = 0
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    @staticmethod
    def _nullable_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        return CalculationService._to_decimal(value)

    @staticmethod
    def _decimal_to_float(value: Any) -> float | None:
        if value is None:
            return None
        return float(CalculationService._to_decimal(value))
