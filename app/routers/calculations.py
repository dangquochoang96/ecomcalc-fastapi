from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.calculations import (
    CalculationCreateRequest,
    CalculationCreateResponse,
    CalculationDetailResponse,
)
from app.services.calculations import CalculationService

router = APIRouter()


@router.post("", response_model=CalculationCreateResponse, status_code=status.HTTP_201_CREATED)
def create_calculation(
    payload: CalculationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CalculationService.create_calculation(db, payload, current_user)


@router.get("/{calculation_id}", response_model=CalculationDetailResponse, status_code=status.HTTP_200_OK)
def get_calculation_detail(
    calculation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CalculationService.get_calculation_detail(db, calculation_id, current_user)
