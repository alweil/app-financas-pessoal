from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.accounts.schemas import AccountCreate, AccountRead
from app.modules.accounts.service import create_account

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountRead)
def create(payload: AccountCreate, db: Session = Depends(get_db)):
    user_id = 1
    return create_account(db, user_id=user_id, payload=payload)
