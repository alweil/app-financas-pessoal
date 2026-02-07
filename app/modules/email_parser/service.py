from sqlalchemy.orm import Session

from app.models import RawEmail
from app.modules.email_parser.schemas import ParsedTransaction, RawEmailIngest, TransactionDraft
from app.modules.transactions.schemas import TransactionCreate


def ingest_email(db: Session, user_id: int, payload: RawEmailIngest) -> RawEmail:
    raw = RawEmail(
        user_id=user_id,
        message_id=payload.message_id,
        from_address=payload.from_address,
        subject=payload.subject,
        body=payload.body,
        bank_source=payload.bank_source,
    )
    db.add(raw)
    db.commit()
    db.refresh(raw)
    return raw


def build_transaction_draft(
    parsed: ParsedTransaction,
    account_id: int,
    category_id: int | None,
) -> TransactionDraft | None:
    if not parsed.success or parsed.amount is None:
        return None
    return TransactionDraft(
        account_id=account_id,
        amount=parsed.amount,
        merchant=parsed.merchant,
        description=parsed.description,
        transaction_date=parsed.transaction_date,
        transaction_type=parsed.transaction_type,
        payment_method=parsed.payment_method,
        card_last4=parsed.card_last4,
        installments_total=parsed.installments_total,
        installments_current=parsed.installments_current,
        category_id=category_id,
    )


def build_transaction_create(
    parsed: ParsedTransaction,
    account_id: int,
    category_id: int | None,
    raw_email_id: int | None,
) -> TransactionCreate | None:
    draft = build_transaction_draft(parsed, account_id, category_id)
    if not draft:
        return None
    return TransactionCreate(
        account_id=draft.account_id,
        amount=draft.amount,
        merchant=draft.merchant,
        description=draft.description,
        transaction_date=draft.transaction_date,
        transaction_type=draft.transaction_type,
        payment_method=draft.payment_method,
        card_last4=draft.card_last4,
        installments_total=draft.installments_total,
        installments_current=draft.installments_current,
        category_id=draft.category_id,
        raw_email_id=raw_email_id,
    )
