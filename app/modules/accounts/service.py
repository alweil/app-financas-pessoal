from sqlalchemy.orm import Session

from app.models import Account, AccountType
from app.modules.accounts.schemas import AccountCreate


def create_account(db: Session, user_id: int, payload: AccountCreate) -> Account:
    account = Account(
        user_id=user_id,
        bank_name=payload.bank_name,
        account_type=AccountType(payload.account_type),
        nickname=payload.nickname,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
