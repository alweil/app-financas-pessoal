from datetime import UTC, datetime

from fastapi.testclient import TestClient


def register_and_login(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "secret123"},
    )
    assert response.status_code == 201

    token_response = client.post(
        "/auth/token",
        data={"username": "user@example.com", "password": "secret123"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def get_category_by_name(categories, name, parent_name=None):
    parent_id = None
    if parent_name:
        parent_id = next(
            (c["id"] for c in categories if c["name"] == parent_name), None
        )
    for category in categories:
        if category["name"] == name:
            if parent_name is None:
                return category
            if category.get("parent_id") == parent_id:
                return category
    return None


def create_account(client: TestClient, headers):
    response = client.post(
        "/accounts/",
        json={"bank_name": "Nubank", "account_type": "checking"},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_category_crud_and_delete_rules(client: TestClient):
    headers = register_and_login(client)

    create_response = client.post(
        "/categories/",
        json={"name": "Custom"},
        headers=headers,
    )
    assert create_response.status_code == 200
    category = create_response.json()

    list_response = client.get("/categories/?limit=200", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert any(item["id"] == category["id"] for item in items)

    get_response = client.get(f"/categories/{category['id']}", headers=headers)
    assert get_response.status_code == 200

    update_response = client.put(
        f"/categories/{category['id']}",
        json={"name": "Custom Updated", "icon": "tag"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Custom Updated"

    delete_response = client.delete(f"/categories/{category['id']}", headers=headers)
    assert delete_response.status_code == 200


def test_category_delete_blocked_when_used(client: TestClient):
    headers = register_and_login(client)
    account = create_account(client, headers)

    category_response = client.post(
        "/categories/",
        json={"name": "Food"},
        headers=headers,
    )
    category = category_response.json()

    transaction_response = client.post(
        "/transactions/",
        json={
            "account_id": account["id"],
            "amount": 25.5,
            "merchant": "Padaria",
            "category_id": category["id"],
        },
        headers=headers,
    )
    assert transaction_response.status_code == 200

    delete_response = client.delete(f"/categories/{category['id']}", headers=headers)
    assert delete_response.status_code == 409


def test_budget_crud(client: TestClient):
    headers = register_and_login(client)

    categories_response = client.get("/categories/?limit=200", headers=headers)
    category_id = categories_response.json()["items"][0]["id"]

    create_response = client.post(
        "/budgets/",
        json={"category_id": category_id, "amount_limit": 1000, "period": "monthly"},
        headers=headers,
    )
    assert create_response.status_code == 200
    budget = create_response.json()

    update_response = client.put(
        f"/budgets/{budget['id']}",
        json={
            "amount_limit": 1200,
            "period": "yearly",
            "start_date": datetime.now(UTC).isoformat(),
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount_limit"] == 1200

    delete_response = client.delete(f"/budgets/{budget['id']}", headers=headers)
    assert delete_response.status_code == 200


def test_auto_categorize_transaction(client: TestClient):
    headers = register_and_login(client)
    account = create_account(client, headers)

    categories_response = client.get("/categories/?limit=200", headers=headers)
    categories = categories_response.json()["items"]
    uber_category = get_category_by_name(
        categories, "Uber/99", parent_name="Transporte"
    )

    create_response = client.post(
        "/transactions/",
        json={
            "account_id": account["id"],
            "amount": 10.0,
            "merchant": "Uber Trip",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    assert create_response.json()["category_id"] == uber_category["id"]

    fallback_response = client.post(
        "/transactions/",
        json={
            "account_id": account["id"],
            "amount": 12.0,
            "merchant": "Unknown Merchant",
        },
        headers=headers,
    )
    assert fallback_response.status_code == 200
    categories_response = client.get("/categories/?limit=200", headers=headers)
    categories = categories_response.json()["items"]
    outros_category = get_category_by_name(categories, "Outros", parent_name="Outros")
    assert fallback_response.json()["category_id"] == outros_category["id"]
