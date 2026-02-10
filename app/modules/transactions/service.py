from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.pagination import paginate_query
from app.models import Account, Transaction
from app.modules.ai_agent.service import categorize_with_db
from app.modules.transactions.schemas import TransactionCreate, TransactionUpdate


def create_transaction(
    db: Session, user_id: int, payload: TransactionCreate
) -> Transaction:
    account = (
        db.query(Account)
        .filter(Account.id == payload.account_id, Account.user_id == user_id)
        .first()
    )
    if not account:
        raise ValueError("Account not found")
    category_id = payload.category_id
    if category_id is None:
        categorization = categorize_with_db(
            db, user_id, payload.merchant, payload.description
        )
        category_id = categorization.category_id

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
        category_id=category_id,
        raw_email_id=payload.raw_email_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def list_transactions(
    db: Session,
    user_id: int,
    skip: int,
    limit: int,
) -> tuple[list[Transaction], int]:
    query = (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == user_id)
    )
    return paginate_query(query, skip=skip, limit=limit)


def list_transactions_filtered(
    db: Session,
    user_id: int,
    skip: int,
    limit: int,
    account_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category_id: int | None = None,
) -> tuple[list[Transaction], int]:
    query = (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == user_id)
    )

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    if start_date is not None:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date is not None:
        query = query.filter(Transaction.transaction_date <= end_date)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    return paginate_query(query, skip=skip, limit=limit)


def get_transaction(
    db: Session, user_id: int, transaction_id: int
) -> Transaction | None:
    return (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == user_id, Transaction.id == transaction_id)
        .first()
    )


def update_transaction(
    db: Session,
    user_id: int,
    transaction_id: int,
    payload: TransactionUpdate,
) -> Transaction | None:
    transaction = get_transaction(db, user_id=user_id, transaction_id=transaction_id)
    if not transaction:
        return None

    if payload.account_id is not None:
        account = (
            db.query(Account)
            .filter(Account.id == payload.account_id, Account.user_id == user_id)
            .first()
        )
        if not account:
            raise ValueError("Account not found")
        transaction.account_id = payload.account_id

    if payload.amount is not None:
        transaction.amount = payload.amount
    if payload.merchant is not None:
        transaction.merchant = payload.merchant
    if payload.description is not None:
        transaction.description = payload.description
    if payload.transaction_date is not None:
        transaction.transaction_date = payload.transaction_date
    if payload.transaction_type is not None:
        transaction.transaction_type = payload.transaction_type
    if payload.payment_method is not None:
        transaction.payment_method = payload.payment_method
    if payload.card_last4 is not None:
        transaction.card_last4 = payload.card_last4
    if payload.installments_total is not None:
        transaction.installments_total = payload.installments_total
    if payload.installments_current is not None:
        transaction.installments_current = payload.installments_current
    if payload.category_id is not None:
        transaction.category_id = payload.category_id

    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, user_id: int, transaction_id: int) -> bool:
    transaction = get_transaction(db, user_id=user_id, transaction_id=transaction_id)
    if not transaction:
        return False
    db.delete(transaction)
    db.commit()
    return True
