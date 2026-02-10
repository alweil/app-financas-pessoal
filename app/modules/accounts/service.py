from sqlalchemy.orm import Session

from app.core.pagination import paginate_query

from app.models import Account, AccountType
from app.modules.accounts.schemas import AccountCreate, AccountUpdate


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


def list_accounts(db: Session, user_id: int, skip: int, limit: int) -> tuple[list[Account], int]:
    query = db.query(Account).filter(Account.user_id == user_id)
    return paginate_query(query, skip=skip, limit=limit)


def get_account(db: Session, user_id: int, account_id: int) -> Account | None:
    return (
        db.query(Account)
        .filter(Account.user_id == user_id, Account.id == account_id)
        .first()
    )


def update_account(
    db: Session,
    user_id: int,
    account_id: int,
    payload: AccountUpdate,
) -> Account | None:
    account = get_account(db, user_id=user_id, account_id=account_id)
    if not account:
        return None

    if payload.bank_name is not None:
        account.bank_name = payload.bank_name
    if payload.account_type is not None:
        account.account_type = AccountType(payload.account_type)
    if payload.nickname is not None:
        account.nickname = payload.nickname

    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, user_id: int, account_id: int) -> bool:
    account = get_account(db, user_id=user_id, account_id=account_id)
    if not account:
        return False
    db.delete(account)
    db.commit()
    return True
