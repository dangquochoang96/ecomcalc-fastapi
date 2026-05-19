from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.categories import ApiResponse, CategoryFeeImportResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services.categories import (
    get_categories_with_hierarchy,
    import_category_fee_documents_from_pdf,
)

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


@router.post(
    "/import-fees",
    response_model=CategoryFeeImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_category_fees(
    file: Optional[UploadFile] = File(
        None, description="Single PDF file. Requires shop_type."
    ),
    shop_type: Optional[str] = Form(None, description="mall or normal"),
    mall_file: Optional[UploadFile] = File(None, description="Shopee Mall PDF file"),
    normal_file: Optional[UploadFile] = File(None, description="Shopee normal PDF file"),
    platform_id: Optional[int] = Form(None),
    platform_fee_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Import Shopee category fixed fee data from PDF.

    Existing categories and category fees for the target platform are replaced once.
    Upload either file + shop_type, or mall_file and/or normal_file.
    """
    try:
        documents = []
        if file is not None:
            if shop_type is None:
                raise ValueError("shop_type is required when using file")
            documents.append((await file.read(), file.filename or "", shop_type))
        if mall_file is not None:
            documents.append((await mall_file.read(), mall_file.filename or "", "mall"))
        if normal_file is not None:
            documents.append(
                (await normal_file.read(), normal_file.filename or "", "normal")
            )

        return import_category_fee_documents_from_pdf(
            db=db,
            documents=documents,
            platform_id=platform_id,
            platform_fee_id=platform_fee_id,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error importing category fees",
                "error": str(e),
            },
        )
