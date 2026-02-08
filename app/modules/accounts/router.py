from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.modules.accounts.schemas import AccountCreate, AccountRead, AccountUpdate
from app.modules.accounts.service import (
    create_account,
    delete_account,
    get_account,
    list_accounts,
    update_account,
)
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


@router.put("/{account_id}", response_model=AccountRead)
def update(
    account_id: int,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = update_account(db, user_id=current_user.id, account_id=account_id, payload=payload)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/{account_id}")
def delete(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = delete_account(db, user_id=current_user.id, account_id=account_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "deleted"}
