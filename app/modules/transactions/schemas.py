from datetime import datetime

from pydantic import BaseModel


class TransactionCreate(BaseModel):
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


class TransactionRead(BaseModel):
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
