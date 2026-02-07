from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.categories.schemas import CategoryCreate, CategoryRead
from app.modules.categories.service import create_category

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryRead)
def create(payload: CategoryCreate, db: Session = Depends(get_db)):
    user_id = 1
    return create_category(db, user_id=user_id, payload=payload)
