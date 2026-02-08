from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.modules.categories.schemas import CategoryCreate, CategoryRead
from app.modules.categories.service import create_category, get_category, list_categories
from app.modules.auth.router import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryRead)
def create(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_category(db, user_id=current_user.id, payload=payload)


@router.get("/", response_model=list[CategoryRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_categories(db, user_id=current_user.id)


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
