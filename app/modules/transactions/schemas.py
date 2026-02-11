from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

TransactionType = Literal["purchase", "pix_in", "pix_out", "unknown"]
PaymentMethod = Literal["credit_card", "debit_card", "pix", "boleto"]


class TransactionCreate(BaseModel):
    account_id: int
    amount: Decimal
    merchant: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None
    transaction_type: TransactionType | None = None
    payment_method: PaymentMethod | None = None
    card_last4: str | None = None
    installments_total: int | None = None
    installments_current: int | None = None
    category_id: int | None = None
    raw_email_id: int | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

    id: int
    account_id: int
    amount: Decimal
    merchant: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None
    transaction_type: TransactionType | None = None
    payment_method: PaymentMethod | None = None
    card_last4: str | None = None
    installments_total: int | None = None
    installments_current: int | None = None
    category_id: int | None = None
    raw_email_id: int | None = None




class TransactionUpdate(BaseModel):
    account_id: int | None = None
    amount: Decimal | None = None
    merchant: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None
    transaction_type: TransactionType | None = None
    payment_method: PaymentMethod | None = None
    card_last4: str | None = None
    installments_total: int | None = None
    installments_current: int | None = None
    category_id: int | None = None


class TransactionListResponse(BaseModel):
    items: list[TransactionRead]
    total: int
    skip: int
    limit: int
