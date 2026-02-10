from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.pagination import PaginationParams, get_pagination_params
from app.models import User
from app.modules.auth.router import get_current_user
from app.modules.transactions.schemas import (
    TransactionCreate,
    TransactionListResponse,
    TransactionRead,
    TransactionUpdate,
)
from app.modules.transactions.service import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    list_transactions_filtered,
    update_transaction,
)

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


@router.get("/", response_model=TransactionListResponse)
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    account_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category_id: int | None = None,
    pagination: PaginationParams = Depends(get_pagination_params),
):
    if account_id is not None or start_date is not None or end_date is not None or category_id is not None:
        items, total = list_transactions_filtered(
            db,
            user_id=current_user.id,
            skip=pagination.skip,
            limit=pagination.limit,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
        )
    else:
        items, total = list_transactions(
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


@router.put("/{transaction_id}", response_model=TransactionRead)
def update(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        transaction = update_transaction(
            db,
            user_id=current_user.id,
            transaction_id=transaction_id,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.delete("/{transaction_id}")
def delete(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = delete_transaction(db, user_id=current_user.id, transaction_id=transaction_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "deleted"}
