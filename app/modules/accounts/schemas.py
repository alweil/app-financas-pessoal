from pydantic import BaseModel


class AccountCreate(BaseModel):
    bank_name: str
    account_type: str
    nickname: str | None = None


class AccountRead(BaseModel):
    id: int
    bank_name: str
    account_type: str
    nickname: str | None = None

    class Config:
        from_attributes = True
