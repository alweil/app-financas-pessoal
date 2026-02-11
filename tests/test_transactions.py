from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def register_and_login(client: TestClient, email: str) -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 201

    token_response = client.post(
        "/auth/token",
        data={"username": email, "password": "secret123"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_account(client: TestClient, headers: dict, bank_name: str) -> dict:
    response = client.post(
        "/accounts/",
        json={"bank_name": bank_name, "account_type": "checking"},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_transaction_crud_and_filters(client: TestClient):
    headers = register_and_login(client, "user@example.com")
    account = create_account(client, headers, "Nubank")

    category_response = client.post(
        "/categories/",
        json={"name": "Custom"},
        headers=headers,
    )
    assert category_response.status_code == 200
    category_id = category_response.json()["id"]

    now = datetime.now(UTC)
    older = now - timedelta(days=3)

    create_response = client.post(
        "/transactions/",
        json={
            "account_id": account["id"],
            "amount": 50.0,
            "merchant": "Padaria Central",
            "transaction_date": older.isoformat(),
            "category_id": category_id,
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    transaction = create_response.json()

    create_response_2 = client.post(
        "/transactions/",
        json={
            "account_id": account["id"],
            "amount": 75.0,
            "merchant": "Mercado X",
            "transaction_date": now.isoformat(),
        },
        headers=headers,
    )
    assert create_response_2.status_code == 200

    list_response = client.get("/transactions/", headers=headers)
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 2

    filtered = client.get(
        "/transactions/",
        headers=headers,
        params={"start_date": now.isoformat(), "end_date": now.isoformat()},
    )
    assert filtered.status_code == 200
    filtered_items = filtered.json()["items"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["amount"] == 75.0

    filtered_by_category = client.get(
        f"/transactions/?category_id={category_id}",
        headers=headers,
    )
    assert filtered_by_category.status_code == 200
    filtered_items = filtered_by_category.json()["items"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["category_id"] == category_id

    update_response = client.put(
        f"/transactions/{transaction['id']}",
        json={"description": "Atualizada", "amount": 55.0},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == 55.0

    get_response = client.get(f"/transactions/{transaction['id']}", headers=headers)
    assert get_response.status_code == 200

    delete_response = client.delete(
        f"/transactions/{transaction['id']}", headers=headers
    )
    assert delete_response.status_code == 200

    missing_response = client.get(f"/transactions/{transaction['id']}", headers=headers)
    assert missing_response.status_code == 404


def test_transaction_account_ownership(client: TestClient):
    headers_user1 = register_and_login(client, "user1@example.com")
    headers_user2 = register_and_login(client, "user2@example.com")

    account_user2 = create_account(client, headers_user2, "Inter")

    create_response = client.post(
        "/transactions/",
        json={
            "account_id": account_user2["id"],
            "amount": 30.0,
            "merchant": "Loja X",
        },
        headers=headers_user1,
    )
    assert create_response.status_code == 404
