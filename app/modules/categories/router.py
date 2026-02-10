from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.pagination import PaginationParams, get_pagination_params
from app.models import User
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryRead,
    CategoryUpdate,
)
from app.modules.categories.service import (
    create_category,
    delete_category,
    get_category,
    list_categories,
    seed_default_categories,
    update_category,
)
from app.modules.auth.router import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryRead)
def create(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_category(db, user_id=current_user.id, payload=payload)


@router.get("/", response_model=CategoryListResponse)
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination_params),
):
    items, total = list_categories(
        db,
        user_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return {
        "items": items,
        "total": total,
        "skip": pagination.skip,
        "limit": pagination.limit,
    }


@router.post("/seed", response_model=list[CategoryRead])
def seed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return seed_default_categories(db, user_id=current_user.id)


@router.get("/{category_id}", response_model=CategoryRead)
def get_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = get_category(db, user_id=current_user.id, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryRead)
def update(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = update_category(db, user_id=current_user.id, category_id=category_id, payload=payload)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/{category_id}")
def delete(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        removed = delete_category(db, user_id=current_user.id, category_id=category_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not removed:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"status": "deleted"}
