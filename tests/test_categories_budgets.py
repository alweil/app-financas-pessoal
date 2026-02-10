from datetime import UTC, datetime

from fastapi.testclient import TestClient


def register_and_login(client: TestClient) -> dict:
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "secret"},
    )
    assert response.status_code == 201

    token_response = client.post(
        "/auth/token",
        data={"username": "user@example.com", "password": "secret"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_account(client: TestClient, headers: dict) -> dict:
    response = client.post(
        "/accounts/",
        json={"bank_name": "Nubank", "account_type": "checking"},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_category_delete_with_children(client: TestClient):
    headers = register_and_login(client)

    parent_response = client.post(
        "/categories/",
        json={"name": "Parent"},
        headers=headers,
    )
    assert parent_response.status_code == 200
    parent = parent_response.json()

    child_response = client.post(
        "/categories/",
        json={"name": "Child", "parent_id": parent["id"]},
        headers=headers,
    )
    assert child_response.status_code == 200
    child = child_response.json()

    delete_parent = client.delete(f"/categories/{parent['id']}", headers=headers)
    assert delete_parent.status_code == 409

    delete_child = client.delete(f"/categories/{child['id']}", headers=headers)
    assert delete_child.status_code == 200

    delete_parent = client.delete(f"/categories/{parent['id']}", headers=headers)
    assert delete_parent.status_code == 200


def test_budget_summary_with_subcategories(client: TestClient):
    headers = register_and_login(client)
    account = create_account(client, headers)

    parent_response = client.post(
        "/categories/",
        json={"name": "Parent Budget"},
        headers=headers,
    )
    parent = parent_response.json()

    child_response = client.post(
        "/categories/",
        json={"name": "Child Budget", "parent_id": parent["id"]},
        headers=headers,
    )
    child = child_response.json()

    budget_response = client.post(
        "/budgets/",
        json={"category_id": parent["id"], "amount_limit": 100.0, "period": "monthly"},
        headers=headers,
    )
    assert budget_response.status_code == 200
    budget = budget_response.json()

    transaction_response = client.post(
        "/transactions/",
        json={
            "account_id": account["id"],
            "amount": 25.0,
            "merchant": "Loja",
            "category_id": child["id"],
            "transaction_date": datetime.now(UTC).isoformat(),
        },
        headers=headers,
    )
    assert transaction_response.status_code == 200

    summary_with_children = client.get(
        f"/budgets/{budget['id']}/summary?include_subcategories=true",
        headers=headers,
    )
    assert summary_with_children.status_code == 200
    assert summary_with_children.json()["amount_spent"] == 25.0

    summary_without = client.get(
        f"/budgets/{budget['id']}/summary?include_subcategories=false",
        headers=headers,
    )
    assert summary_without.status_code == 200
    assert summary_without.json()["amount_spent"] == 0.0
