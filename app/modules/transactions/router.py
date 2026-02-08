from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.modules.auth.router import get_current_user
from app.modules.transactions.schemas import TransactionCreate, TransactionRead
from app.modules.transactions.service import create_transaction, get_transaction, list_transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionRead)
def create(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_transaction(db, user_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/", response_model=list[TransactionRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_transactions(db, user_id=current_user.id)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_by_id(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = get_transaction(db, user_id=current_user.id, transaction_id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction
