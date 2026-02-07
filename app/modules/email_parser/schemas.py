from datetime import datetime

from pydantic import BaseModel


class RawEmailIngest(BaseModel):
    message_id: str
    from_address: str
    subject: str | None = None
    body: str
    bank_source: str | None = None


class ParsedTransaction(BaseModel):
    success: bool
    bank_source: str | None
    amount: float | None
    merchant: str | None
    transaction_type: str | None
    payment_method: str | None
    card_last4: str | None = None
    installments_total: int | None = None
    installments_current: int | None = None
    transaction_date: datetime | None
    description: str | None
    subject: str | None
    reason: str | None = None


class TransactionDraft(BaseModel):
    account_id: int
    amount: float
    merchant: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None
    transaction_type: str | None = None
    payment_method: str | None = None
    card_last4: str | None = None
    installments_total: int | None = None
    installments_current: int | None = None
    category_id: int | None = None


class ParseToTransactionRequest(BaseModel):
    account_id: int
    category_id: int | None = None
    email: RawEmailIngest


class ParseToTransactionResponse(BaseModel):
    parsed: ParsedTransaction
    transaction: TransactionDraft | None = None


class TransactionCreated(BaseModel):
    id: int
    account_id: int
    amount: float
    merchant: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None
    transaction_type: str | None = None
    payment_method: str | None = None
    card_last4: str | None = None
    installments_total: int | None = None
    installments_current: int | None = None
    category_id: int | None = None
    raw_email_id: int | None = None

    class Config:
        from_attributes = True


class ParseAndCreateResponse(BaseModel):
    parsed: ParsedTransaction
    transaction: TransactionCreated | None = None
