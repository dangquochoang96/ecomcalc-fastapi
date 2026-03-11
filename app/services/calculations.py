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
        selected_fee_ids = [fee.fee_id for fee in payload.fee_config if fee.is_applied]
        platform_fee_map = {}
        category_fee_map = {}

        if selected_fee_ids:
            platform_fees = (
                db.query(PlatformFee)
                .filter(
                    PlatformFee.platform_id == payload.platform_id,
                    PlatformFee.id.in_(selected_fee_ids),
                    PlatformFee.is_active.is_(True),
                )
                .all()
            )
            platform_fee_map = {fee.id: fee for fee in platform_fees}
            missing_fee_ids = sorted(set(selected_fee_ids) - set(platform_fee_map.keys()))
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
                        CategoryFee.platform_fee_id.in_(selected_fee_ids),
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
                    "fee_name": fee.fee_name,
                    "fee_type": fee.fee_type,
                    "is_applied": fee.is_applied,
                    "custom_value": CalculationService._decimal_to_float(fee.custom_value),
                    "note": CalculationService._build_fee_note(fee, platform_fee),
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
                if not fee.is_applied:
                    continue

                platform_fee = platform_fee_map.get(fee.fee_id)
                category_fee = category_fee_map.get((fee.fee_id, product.category_id))
                fee_value, rate_value, breakdown_type = CalculationService._resolve_fee_value(
                    selling_price=selling_price,
                    fee_type=fee.fee_type,
                    custom_value=fee.custom_value,
                    platform_fee=platform_fee,
                    category_fee=category_fee,
                )
                fee_key = CalculationService._resolve_fee_key(
                    fee_name=fee.fee_name,
                    fee_code=getattr(platform_fee, "fee_code", None),
                    fee_id=fee.fee_id,
                )
                breakdown[fee_key] = {
                    "name": fee.fee_name,
                    "value": CalculationService._decimal_to_float(fee_value),
                    "type": breakdown_type,
                }
                if rate_value is not None:
                    breakdown[fee_key]["rate"] = CalculationService._decimal_to_float(
                        rate_value
                    )
                if category_fee and product.category:
                    breakdown[fee_key]["category"] = product.category.category_name

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
                    "fees_applied": calculation.fee_config or [],
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
        fee_type: str,
        custom_value: Decimal | None,
        platform_fee: PlatformFee | None,
        category_fee: CategoryFee | None,
    ) -> tuple[Decimal, Decimal | None, str]:
        normalized_type = (fee_type or "").strip().lower()
        configured_value = custom_value
        breakdown_type = normalized_type or "custom"

        if category_fee is not None:
            configured_value = CalculationService._to_decimal(category_fee.fee_value)
            breakdown_type = "category_based"
        elif configured_value is not None:
            configured_value = CalculationService._to_decimal(configured_value)
        elif platform_fee is not None:
            configured_value = CalculationService._to_decimal(platform_fee.default_value)
            breakdown_type = "default"
        else:
            configured_value = Decimal("0")

        if CalculationService._is_percentage_fee(normalized_type, platform_fee):
            fee_value = (selling_price * configured_value) / HUNDRED
            return (
                CalculationService._to_decimal(fee_value),
                CalculationService._to_decimal(configured_value),
                breakdown_type,
            )

        return CalculationService._to_decimal(configured_value), None, breakdown_type

    @staticmethod
    def _build_fee_note(fee: Any, platform_fee: PlatformFee | None) -> str | None:
        if not fee.is_applied:
            return "Skipped in this calculation"
        if fee.custom_value is not None:
            return "Applied custom value"
        if platform_fee is not None:
            return "Applied default platform value"
        return None

    @staticmethod
    def _resolve_fee_key(fee_name: str, fee_code: str | None, fee_id: int) -> str:
        raw_value = f"{fee_name} {fee_code or ''}".lower()
        if "commission" in raw_value or "hoa hong" in raw_value:
            return "commission"
        if "shipping" in raw_value or "van chuyen" in raw_value:
            return "shipping"
        if "payment" in raw_value or "thanh toan" in raw_value:
            return "payment"
        return fee_code.lower() if fee_code else f"fee_{fee_id}"

    @staticmethod
    def _is_percentage_fee(fee_type: str, platform_fee: PlatformFee | None) -> bool:
        if fee_type in {
            "percent",
            "percentage",
            "rate",
            "ratio",
            "category",
            "category_based",
            "percent_based",
        }:
            return True
        if fee_type in {"fixed", "flat", "amount", "money"}:
            return False
        if platform_fee is None:
            return False
        return str(platform_fee.fee_type) in {"2", "3"}

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if value is None:
            value = 0
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    @staticmethod
    def _decimal_to_float(value: Any) -> float | None:
        if value is None:
            return None
        return float(CalculationService._to_decimal(value))
