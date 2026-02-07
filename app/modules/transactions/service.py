from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Transaction
from app.modules.transactions.schemas import TransactionCreate


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    transaction = Transaction(
        account_id=payload.account_id,
        amount=payload.amount,
        merchant=payload.merchant,
        description=payload.description,
        transaction_date=payload.transaction_date or datetime.utcnow(),
        transaction_type=payload.transaction_type,
        payment_method=payload.payment_method,
        card_last4=payload.card_last4,
        installments_total=payload.installments_total,
        installments_current=payload.installments_current,
        category_id=payload.category_id,
        raw_email_id=payload.raw_email_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
