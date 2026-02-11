from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.modules.transactions.schemas import PaymentMethod, TransactionType


class RawEmailIngest(BaseModel):
    message_id: str
    from_address: str
    subject: str | None = None
    body: str
    bank_source: str | None = None


class ParsedTransaction(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: float})

    success: bool
    bank_source: str | None
    amount: Decimal | None
    merchant: str | None
    transaction_type: TransactionType | None
    payment_method: PaymentMethod | None
    card_last4: str | None = None
    installments_total: int | None = None
    installments_current: int | None = None
    transaction_date: datetime | None
    description: str | None
    subject: str | None
    reason: str | None = None


class TransactionDraft(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: float})

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


class ParseToTransactionRequest(BaseModel):
    account_id: int
    category_id: int | None = None
    email: RawEmailIngest


class ParseToTransactionResponse(BaseModel):
    parsed: ParsedTransaction
    transaction: TransactionDraft | None = None


class TransactionCreated(BaseModel):
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


class ParseAndCreateResponse(BaseModel):
    parsed: ParsedTransaction
    transaction: TransactionCreated | None = None
