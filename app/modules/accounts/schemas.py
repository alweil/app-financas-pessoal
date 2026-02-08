from pydantic import BaseModel

from app.models import AccountType


class AccountCreate(BaseModel):
    bank_name: str
    account_type: AccountType
    nickname: str | None = None


class AccountRead(BaseModel):
    id: int
    bank_name: str
    account_type: AccountType
    nickname: str | None = None

    class Config:
        from_attributes = True


class AccountUpdate(BaseModel):
    bank_name: str | None = None
    account_type: AccountType | None = None
    nickname: str | None = None
