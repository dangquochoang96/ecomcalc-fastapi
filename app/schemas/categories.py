from pydantic import BaseModel
from typing import List, Optional


class CategoryBase(BaseModel):
    category_name: str
    category_code: Optional[str] = None
    level: Optional[int] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True


class CategoryFeeBase(BaseModel):
    fee_value: float

    class Config:
        from_attributes = True


class CategoryFeeResponse(CategoryFeeBase):
    id: int

    class Config:
        from_attributes = True


class CategoryChildrenResponse(BaseModel):
    id: int
    category_name: str
    category_code: Optional[str]
    level: Optional[int]
    parent_id: Optional[int]
    description: Optional[str]
    is_active: bool
    has_children: bool = False
    category_fees: List[CategoryFeeResponse] = []
    children: List["CategoryChildrenResponse"] = []

    class Config:
        from_attributes = True


class CategoryResponse(CategoryBase):
    id: int
    has_children: bool = False
    children: List[CategoryChildrenResponse] = []

    class Config:
        from_attributes = True


class CategoryIndexRequest(BaseModel):
    level: Optional[int] = None
    parent_id: Optional[int] = None


class ApiResponse(BaseModel):
    success: bool
    data: List[CategoryResponse]
    message: Optional[str] = None
