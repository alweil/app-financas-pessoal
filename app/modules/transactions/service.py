from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Account, Transaction
from app.modules.transactions.schemas import TransactionCreate


def create_transaction(db: Session, user_id: int, payload: TransactionCreate) -> Transaction:
    account = (
        db.query(Account)
        .filter(Account.id == payload.account_id, Account.user_id == user_id)
        .first()
    )
    if not account:
        raise ValueError("Account not found")
    transaction = Transaction(
        account_id=payload.account_id,
        amount=payload.amount,
        merchant=payload.merchant,
        description=payload.description,
        transaction_date=payload.transaction_date or datetime.now(UTC),
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


def list_transactions(db: Session, user_id: int) -> list[Transaction]:
    return (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == user_id)
        .all()
    )


def get_transaction(db: Session, user_id: int, transaction_id: int) -> Transaction | None:
    return (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == user_id, Transaction.id == transaction_id)
        .first()
    )
