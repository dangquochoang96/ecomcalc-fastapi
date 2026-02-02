from app.schemas.platform_fees import ApiResponse, ApiPlatformResponse
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import platform_fees as service

router = APIRouter()


@router.get("/", response_model=ApiResponse, status_code=status.HTTP_200_OK)
def read_platform_fees(db: Session = Depends(get_db)):
    """
    Retrieve all active platform fees.
    """
    result = service.get_all_platform_fees(db)
    return ApiResponse(success=True, data=result)


@router.get(
    "/platform", response_model=ApiPlatformResponse, status_code=status.HTTP_200_OK
)
def read_platform(db: Session = Depends(get_db)):
    """
    Retrieve all active platform fees.
    """
    result = service.get_all_platform(db)
    return ApiPlatformResponse(success=True, data=result)
