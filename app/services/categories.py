from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

import json
from app.models.categories import Category, CategoryFee
from app.utils.redis import get_redis_client


def get_categories_with_hierarchy(
    db: Session, level: Optional[int] = None, parent_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get categories with filtering and hierarchical structure - Optimized version

    Args:
        db: Database session
        level: Filter by level (optional)
        parent_id: Filter by parent ID (optional)

    Returns:
        List of categories with their children and fees
    """
    # Try to get from cache
    try:
        redis_client = get_redis_client()
        cache_key = f"categories:hierarchy:v2:{level}:{parent_id}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        print(f"Redis error: {e}")

    # Get parent categories based on filters
    parent_query = db.query(Category)

    # Apply filters for parent categories
    if level is not None:
        parent_query = parent_query.filter(Category.level == level)
    if parent_id is not None:
        parent_query = parent_query.filter(Category.parent_id == parent_id)

    # If no filters provided, default to level 1 categories
    if level is None and parent_id is None:
        parent_query = parent_query.filter(Category.level == 1)

    parent_categories = parent_query.all()

    if not parent_categories:
        return []

    # Get all category IDs to fetch their children and fees
    parent_ids = [cat.id for cat in parent_categories]

    # Single query to get children and fees for all parents
    # Get children categories
    children_query = db.query(Category).filter(Category.parent_id.in_(parent_ids))
    children_categories = children_query.all()

    # Get grandchildren categories (Level 3)
    child_ids = [child.id for child in children_categories]
    grand_children_categories = []
    if child_ids:
        grand_children_query = db.query(Category).filter(
            Category.parent_id.in_(child_ids)
        )
        grand_children_categories = grand_children_query.all()

    # Get all category IDs (parents + children + grandchildren) for fees
    grand_child_ids = [child.id for child in grand_children_categories]
    all_category_ids = parent_ids + child_ids + grand_child_ids

    # Get fees for all categories
    fees_query = db.query(
        CategoryFee.category_id, CategoryFee.id, CategoryFee.fee_value
    ).filter(CategoryFee.category_id.in_(all_category_ids))

    fees_result = fees_query.all()

    # Build lookup dictionaries
    children_dict = {}  # parent_id -> [children]
    fees_dict = {}  # category_id -> [fees]

    # Populate children dictionary
    all_descendants = children_categories + grand_children_categories
    for child in all_descendants:
        if child.parent_id not in children_dict:
            children_dict[child.parent_id] = []
        children_dict[child.parent_id].append(child)

    # Populate fees dictionary
    for fee_row in fees_result:
        cat_id = fee_row.category_id
        if cat_id not in fees_dict:
            fees_dict[cat_id] = []
        fees_dict[cat_id].append(
            {"id": fee_row.id, "fee_value": float(fee_row.fee_value)}
        )

    # Build final response with children and fees
    result_categories = []

    for parent_cat in parent_categories:
        # Build parent category data
        parent_data = {
            "id": parent_cat.id,
            "category_name": parent_cat.category_name,
            "category_code": parent_cat.category_code,
            "level": parent_cat.level,
            "parent_id": parent_cat.parent_id,
            "description": parent_cat.description,
            "is_active": parent_cat.is_active,
            "has_children": parent_cat.id in children_dict
            and len(children_dict[parent_cat.id]) > 0,
            "category_fees": fees_dict.get(parent_cat.id, []),
            "children": [],
        }

        # Add children if exist
        if parent_cat.id in children_dict:
            for child_cat in children_dict[parent_cat.id]:
                child_data = {
                    "id": child_cat.id,
                    "category_name": child_cat.category_name,
                    "category_code": child_cat.category_code,
                    "level": child_cat.level,
                    "parent_id": child_cat.parent_id,
                    "description": child_cat.description,
                    "is_active": child_cat.is_active,
                    "has_children": child_cat.id in children_dict
                    and len(children_dict[child_cat.id]) > 0,
                    "category_fees": fees_dict.get(child_cat.id, []),
                    "children": [],
                }

                # Add grandchildren (Level 3) if exist
                if child_cat.id in children_dict:
                    for grandchild_cat in children_dict[child_cat.id]:
                        grandchild_data = {
                            "id": grandchild_cat.id,
                            "category_name": grandchild_cat.category_name,
                            "category_code": grandchild_cat.category_code,
                            "level": grandchild_cat.level,
                            "parent_id": grandchild_cat.parent_id,
                            "description": grandchild_cat.description,
                            "is_active": grandchild_cat.is_active,
                            "has_children": grandchild_cat.id in children_dict
                            and len(children_dict[grandchild_cat.id]) > 0,
                            "category_fees": fees_dict.get(grandchild_cat.id, []),
                            "children": [],
                        }
                        child_data["children"].append(grandchild_data)

                parent_data["children"].append(child_data)

        result_categories.append(parent_data)

    # Cache the result
    try:
        if redis_client:
            redis_client.setex(cache_key, 3600, json.dumps(result_categories))
    except Exception as e:
        print(f"Redis set error: {e}")

    return result_categories
