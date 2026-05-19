import hashlib
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

import json
from app.models.categories import Category, CategoryFee
from app.models.platform_fees import Platform, PlatformFee
from app.models.products import Product
from app.models.user_platform import UserPlatform
from app.utils.redis import get_redis_client

SHOP_TYPE_NORMAL = 1
SHOP_TYPE_MALL = 2
FIXED_FEE_TYPE = 2
TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class ParsedCategoryFee:
    path: tuple[str, ...]
    fee_value: Decimal


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


def import_category_fees_from_pdf(
    *,
    db: Session,
    file_content: bytes,
    filename: str,
    shop_type_value: str,
    platform_id: int | None = None,
    platform_fee_id: int | None = None,
) -> dict[str, Any]:
    return import_category_fee_documents_from_pdf(
        db=db,
        documents=[(file_content, filename, shop_type_value)],
        platform_id=platform_id,
        platform_fee_id=platform_fee_id,
    )


def import_category_fee_documents_from_pdf(
    *,
    db: Session,
    documents: list[tuple[bytes, str, str]],
    platform_id: int | None = None,
    platform_fee_id: int | None = None,
) -> dict[str, Any]:
    if not documents:
        raise ValueError("At least one PDF file is required")

    platform = _resolve_platform(db, platform_id)
    platform_fee = _resolve_platform_fee(db, platform.id, platform_fee_id)
    parsed_documents: list[tuple[int, list[ParsedCategoryFee]]] = []

    for file_content, filename, shop_type_value in documents:
        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported")
        if not file_content:
            raise ValueError(f"Uploaded file is empty: {filename}")

        shop_type = _parse_shop_type(shop_type_value)
        parsed_rows = _parse_pdf_category_fees(file_content)
        if not parsed_rows:
            raise ValueError(f"No category fee rows were found in {filename}")
        parsed_documents.append((shop_type, parsed_rows))

    _replace_platform_categories(db, platform.id)
    category_cache: dict[tuple[str, ...], Category] = {}
    fee_cache: set[tuple[int, int]] = set()
    fees_created = 0

    for shop_type, parsed_rows in parsed_documents:
        for row in parsed_rows:
            parent_id = None
            current_path: list[str] = []
            category = None

            for level, category_name in enumerate(row.path, start=1):
                current_path.append(category_name)
                path_key = tuple(current_path)
                category = category_cache.get(path_key)
                if category is None:
                    category = Category(
                        platform_id=platform.id,
                        category_name=category_name,
                        category_code=_build_category_code(path_key),
                        level=level,
                        parent_id=parent_id,
                        is_active=True,
                    )
                    db.add(category)
                    db.flush()
                    category_cache[path_key] = category
                parent_id = category.id

            if category is None:
                continue

            fee_key = (shop_type, category.id)
            if fee_key in fee_cache:
                continue
            fee_cache.add(fee_key)
            db.add(
                CategoryFee(
                    platform_fee_id=platform_fee.id,
                    category_id=category.id,
                    shop_type=shop_type,
                    fee_value=row.fee_value,
                )
            )
            fees_created += 1

    db.commit()
    _clear_category_cache()

    return {
        "success": True,
        "message": "Import category fees successfully",
        "platform_id": platform.id,
        "platform_fee_id": platform_fee.id,
        "shop_type": parsed_documents[0][0] if len(parsed_documents) == 1 else 0,
        "categories_created": len(category_cache),
        "fees_created": fees_created,
    }


def _parse_shop_type(value: str) -> int:
    normalized = _normalize_text(value).lower()
    if normalized in {"mall", "shopee mall", "2"}:
        return SHOP_TYPE_MALL
    if normalized in {"normal", "regular", "thuong", "shopee thuong", "1"}:
        return SHOP_TYPE_NORMAL
    raise ValueError("shop_type must be one of: mall, normal")


def _resolve_platform(db: Session, platform_id: int | None) -> Platform:
    query = db.query(Platform).filter(Platform.is_active.is_(True))
    if platform_id is not None:
        platform = query.filter(Platform.id == platform_id).first()
    else:
        platform = (
            query.filter(
                (Platform.code.ilike("%shopee%")) | (Platform.name.ilike("%shopee%"))
            )
            .order_by(Platform.id.asc())
            .first()
        )
    if not platform:
        raise ValueError("Shopee platform was not found; please provide platform_id")
    return platform


def _resolve_platform_fee(
    db: Session, platform_id: int, platform_fee_id: int | None
) -> PlatformFee:
    query = db.query(PlatformFee).filter(
        PlatformFee.platform_id == platform_id,
        PlatformFee.is_active.is_(True),
    )
    if platform_fee_id is not None:
        platform_fee = query.filter(PlatformFee.id == platform_fee_id).first()
    else:
        platform_fee = (
            query.filter(
                PlatformFee.fee_type == FIXED_FEE_TYPE,
                (
                    PlatformFee.fee_code.ilike("%fixed%")
                    | PlatformFee.fee_code.ilike("%co_dinh%")
                    | PlatformFee.fee_name.ilike("%fixed%")
                    | PlatformFee.fee_name.ilike("%co dinh%")
                ),
            )
            .order_by(PlatformFee.id.asc())
            .first()
        )
    if not platform_fee:
        raise ValueError(
            "Fixed platform fee was not found; please provide platform_fee_id"
        )
    return platform_fee


def _replace_platform_categories(db: Session, platform_id: int) -> None:
    category_ids = [
        row[0] for row in db.query(Category.id).filter(Category.platform_id == platform_id)
    ]
    if not category_ids:
        return

    db.query(UserPlatform).filter(UserPlatform.category_id.in_(category_ids)).update(
        {UserPlatform.category_id: None}, synchronize_session=False
    )
    db.query(Product).filter(Product.category_id.in_(category_ids)).update(
        {Product.category_id: None}, synchronize_session=False
    )
    db.query(Category).filter(Category.parent_id.in_(category_ids)).update(
        {Category.parent_id: None}, synchronize_session=False
    )
    db.query(CategoryFee).filter(CategoryFee.category_id.in_(category_ids)).delete(
        synchronize_session=False
    )
    db.query(Category).filter(Category.id.in_(category_ids)).delete(
        synchronize_session=False
    )
    db.flush()


def _parse_pdf_category_fees(file_content: bytes) -> list[ParsedCategoryFee]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise ValueError(
            "Missing dependency pdfplumber. Please install requirements.txt"
        ) from exc

    table_rows = _parse_pdf_tables(file_content, pdfplumber)
    if table_rows:
        return table_rows

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("Missing dependency pypdf. Please install requirements.txt") from exc

    reader = PdfReader(BytesIO(file_content))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            text_parts.append(page_text)

    return _parse_category_fee_text("\n".join(text_parts))


def _parse_pdf_tables(file_content: bytes, pdfplumber: Any) -> list[ParsedCategoryFee]:
    rows: list[ParsedCategoryFee] = []
    seen: set[tuple[tuple[str, ...], Decimal]] = set()

    with pdfplumber.open(BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                for raw_row in table:
                    parsed_row = _parse_table_row(raw_row or [])
                    if parsed_row is None:
                        continue
                    row_key = (parsed_row.path, parsed_row.fee_value)
                    if row_key in seen:
                        continue
                    seen.add(row_key)
                    rows.append(parsed_row)

    return rows


def _parse_table_row(raw_row: list[Any]) -> ParsedCategoryFee | None:
    cells = [_clean_cell(cell) for cell in raw_row]
    cells = [cell for cell in cells if cell]

    if len(cells) < 3 or _is_noise_line(" ".join(cells)):
        return None

    fee_index = None
    fee_value = None
    for index in range(len(cells) - 1, -1, -1):
        fee_match = re.search(r"(\d+(?:[,.]\d+)?)\s*%", cells[index])
        if fee_match:
            fee_index = index
            fee_value = Decimal(fee_match.group(1).replace(",", ".")).quantize(
                TWOPLACES, rounding=ROUND_HALF_UP
            )
            break

    if fee_index is None or fee_value is None:
        return None

    category_cells = cells[:fee_index]
    if category_cells and re.fullmatch(r"\d+", category_cells[0]):
        category_cells = category_cells[1:]

    path = tuple(
        _clean_category_name(cell)
        for cell in category_cells[:3]
        if _clean_category_name(cell)
    )
    if not path:
        return None

    return ParsedCategoryFee(path=path, fee_value=fee_value)


def _parse_category_fee_text(text: str) -> list[ParsedCategoryFee]:
    rows: list[ParsedCategoryFee] = []
    seen: set[tuple[tuple[str, ...], Decimal]] = set()
    pending_lines: list[str] = []

    for raw_line in text.splitlines():
        line = _clean_line(raw_line)
        if not line or _is_noise_line(line):
            continue

        fee_match = re.search(r"(\d+(?:[,.]\d+)?)\s*%", line)
        if not fee_match:
            pending_lines.append(line)
            pending_lines = pending_lines[-4:]
            continue

        fee_value = Decimal(fee_match.group(1).replace(",", ".")).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        before_fee = line[: fee_match.start()].strip()
        after_fee = line[fee_match.end() :].strip()
        candidate_text = " ".join([*pending_lines, before_fee]).strip()

        path = _extract_category_path(candidate_text)
        pending_lines = [after_fee] if after_fee and not _is_noise_line(after_fee) else []

        if not path:
            continue

        row_key = (path, fee_value)
        if row_key in seen:
            continue
        seen.add(row_key)
        rows.append(ParsedCategoryFee(path=path, fee_value=fee_value))

    return rows


def _extract_category_path(value: str) -> tuple[str, ...]:
    value = value.strip(" -:;|")
    if not value:
        return tuple()

    value = re.sub(r"^\d+(?:[\.)])?\s+", "", value)
    parts = [
        _clean_category_name(part)
        for part in re.split(r"\s{2,}|\t+|\s+[>/]\s+|\s+-\s+", value)
    ]
    parts = [part for part in parts if part and not _is_noise_line(part)]

    if len(parts) == 1:
        compact_parts = re.split(r"\s{2,}", value)
        if len(compact_parts) > 1:
            parts = [_clean_category_name(part) for part in compact_parts if part]

    return tuple(parts[:4])


def _clean_line(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = re.sub(r"\t+", "  ", value)
    return value.strip()


def _clean_cell(value: Any) -> str:
    if value is None:
        return ""
    value = str(value).replace("\u00a0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _clean_category_name(value: str) -> str:
    value = _clean_line(value)
    value = re.sub(r"^\d+[\.)]\s*", "", value)
    value = re.sub(r"\s*\(\s*$", "", value)
    return value.strip(" -:;|")


def _is_noise_line(value: str) -> bool:
    normalized = _normalize_text(value).lower()
    noise_keywords = (
        "nganh hang",
        "phi co dinh",
        "da bao gom vat",
        "trang ",
        "page ",
        "shopee",
        "ap dung",
        "cap 1",
        "cap 2",
        "cap 3",
        "stt",
    )
    return any(keyword in normalized for keyword in noise_keywords)


def _build_category_code(path: tuple[str, ...]) -> str:
    slug = _slugify(path[-1])[:40] or "category"
    digest = hashlib.sha1(" > ".join(path).encode("utf-8")).hexdigest()[:10]
    return f"{slug}_{digest}"


def _slugify(value: str) -> str:
    normalized = _normalize_text(value).lower()
    slug = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return slug or "category"


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    return "".join(char for char in value if not unicodedata.combining(char))


def _clear_category_cache() -> None:
    try:
        redis_client = get_redis_client()
        for key in redis_client.scan_iter("categories:hierarchy:v2:*"):
            redis_client.delete(key)
    except Exception as e:
        print(f"Redis clear category cache error: {e}")
