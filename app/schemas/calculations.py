from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class CalculationProductCreate(BaseModel):
    product_id: int
    selling_price: Decimal = Field(..., ge=0)


class FeeConfigCreate(BaseModel):
    fee_id: int
    custom_value: Optional[Decimal] = Field(default=None, ge=0)
    min_value: Optional[Decimal] = Field(default=None, ge=0)
    max_value: Optional[Decimal] = Field(default=None, ge=0)


class CalculationCreateRequest(BaseModel):
    calculation_name: Optional[str] = None
    notes: Optional[str] = None
    platform_id: int
    products: list[CalculationProductCreate]
    fee_config: list[FeeConfigCreate]


class CalculationCreateSummary(BaseModel):
    total_products: int
    total_revenue: Decimal
    total_fees: Decimal
    total_profit: Decimal
    avg_profit_margin: Decimal


class CalculationCreateData(BaseModel):
    calculation_id: int
    summary: CalculationCreateSummary


class CalculationCreateResponse(BaseModel):
    success: bool = True
    message: str = "Tinh toan thanh cong"
    data: CalculationCreateData


class CalculationPlatformResponse(BaseModel):
    id: int
    name: str
    code: str


class FeeAppliedResponse(BaseModel):
    fee_id: int
    fee_name: str
    fee_type: int
    custom_value: Optional[Decimal] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None


class CalculationInfoResponse(BaseModel):
    id: int
    calculation_name: Optional[str] = None
    calculation_date: datetime
    notes: Optional[str] = None
    platform: CalculationPlatformResponse
    fees_applied: list[FeeAppliedResponse]


class CalculationSummaryResponse(BaseModel):
    total_products: int
    total_revenue: Decimal
    total_cost: Decimal
    total_fees: Decimal
    total_profit: Decimal
    avg_profit_margin: Decimal
    profitable_products: int
    loss_products: int


class ProductCalculationResultResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: Optional[str] = None
    category_name: Optional[str] = None
    cost_price: Decimal
    selling_price: Decimal
    total_fees: Decimal
    net_profit: Decimal
    profit_margin: Decimal
    status: str
    fee_breakdown: dict[str, Any]


class CalculationDetailData(BaseModel):
    calculation: CalculationInfoResponse
    summary: CalculationSummaryResponse
    products: list[ProductCalculationResultResponse]


class CalculationDetailResponse(BaseModel):
    success: bool = True
    data: CalculationDetailData
