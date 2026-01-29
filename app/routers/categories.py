from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.categories import ApiResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services.categories import get_categories_with_hierarchy

router = APIRouter()


@router.get("/", response_model=ApiResponse)
def get_categories(
    level: Optional[int] = Query(None, description="Filter by level"),
    parent_id: Optional[int] = Query(None, description="Filter by parent ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get categories with filtering and hierarchical structure - Optimized version
    """
    try:
        result_categories = get_categories_with_hierarchy(
            db=db, level=level, parent_id=parent_id
        )

        return ApiResponse(success=True, data=result_categories)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Error retrieving categories",
                "error": str(e),
            },
        )
