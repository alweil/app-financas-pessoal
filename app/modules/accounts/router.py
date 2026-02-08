from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.modules.accounts.schemas import AccountCreate, AccountRead
from app.modules.accounts.service import create_account, get_account, list_accounts
from app.modules.auth.router import get_current_user

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/", response_model=AccountRead)
def create(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_account(db, user_id=current_user.id, payload=payload)


@router.get("/", response_model=list[AccountRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_accounts(db, user_id=current_user.id)


@router.get("/{account_id}", response_model=AccountRead)
def get_by_id(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = get_account(db, user_id=current_user.id, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
