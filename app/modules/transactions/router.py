from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.transactions.schemas import TransactionCreate, TransactionRead
from app.modules.transactions.service import create_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionRead)
def create(payload: TransactionCreate, db: Session = Depends(get_db)):
    return create_transaction(db, payload)
