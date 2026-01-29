from app.schemas.platform_fees import ApiResponse
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services import platform_fees as service
from app.schemas.platform_fees import PlatformFeeResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def read_platform_fees(db: Session = Depends(get_db)):
    """
    Retrieve all active platform fees.
    """
    result = service.get_all_platform_fees(db)
    return ApiResponse(success=True, data=result)
