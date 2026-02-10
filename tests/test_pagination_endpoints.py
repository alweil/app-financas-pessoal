from datetime import UTC, datetime

import pytest

from app.models import Account, Budget, BudgetPeriod, Category, Transaction, User


def auth_headers(client):
    register = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "secret"},
    )
    assert register.status_code == 201
    token_response = client.post(
        "/auth/token",
        data={"username": "user@example.com", "password": "secret"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, "user@example.com"


def create_account(db_session, user_id: int, name: str) -> Account:
    account = Account(user_id=user_id, bank_name=name, account_type="checking")
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


def create_budget(db_session, user_id: int, category_id: int, amount: float) -> Budget:
    budget = Budget(
        user_id=user_id,
        category_id=category_id,
        amount_limit=amount,
        period=BudgetPeriod.monthly,
        start_date=datetime.now(UTC),
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    return budget


def create_transaction(db_session, account_id: int, amount: float) -> Transaction:
    transaction = Transaction(account_id=account_id, amount=amount, transaction_date=datetime.now(UTC))
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction


@pytest.mark.usefixtures("client", "db_session")
class TestPagination:
    def test_categories_pagination(self, client, db_session):
        headers, email = auth_headers(client)
        user = db_session.query(User).filter(User.email == email).first()
        categories = (
            db_session.query(Category)
            .filter(Category.user_id == user.id, Category.parent_id.is_(None))
            .all()
        )
        assert len(categories) > 1

        response = client.get("/categories/?skip=1&limit=1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["skip"] == 1
        assert data["limit"] == 1
        assert len(data["items"]) == 1

    def test_transactions_pagination(self, client, db_session):
        headers, email = auth_headers(client)
        user = db_session.query(User).filter(User.email == email).first()

        account = create_account(db_session, user_id=user.id, name="Nubank")
        for amount in [10.0, 20.0, 30.0]:
            create_transaction(db_session, account_id=account.id, amount=amount)

        response = client.get("/transactions/?skip=1&limit=1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["skip"] == 1
        assert data["limit"] == 1
        assert len(data["items"]) == 1

    def test_budgets_pagination(self, client, db_session):
        headers, email = auth_headers(client)
        user = db_session.query(User).filter(User.email == email).first()
        categories = (
            db_session.query(Category)
            .filter(Category.user_id == user.id, Category.parent_id.is_(None))
            .all()
        )
        category_id = categories[0].id

        for amount in [100.0, 200.0, 300.0]:
            create_budget(db_session, user_id=user.id, category_id=category_id, amount=amount)

        response = client.get("/budgets/?skip=1&limit=1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["skip"] == 1
        assert data["limit"] == 1
        assert len(data["items"]) == 1
