from datetime import datetime


def register_and_login(client):
    resp = client.post(
        "/auth/register", json={"email": "tx_user@example.com", "password": "secret"}
    )
    assert resp.status_code == 201
    token_resp = client.post(
        "/auth/token", data={"username": "tx_user@example.com", "password": "secret"}
    )
    assert token_resp.status_code == 200
    return token_resp.json()["access_token"]


def test_transaction_category_flow(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # create an account
    acct = client.post(
        "/accounts/",
        json={"bank_name": "TestBank", "account_type": "checking"},
        headers=headers,
    )
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    # create a category
    cat = client.post("/categories/", json={"name": "Groceries"}, headers=headers)
    assert cat.status_code == 200
    category_id = cat.json()["id"]

    # create a transaction with that category
    payload = {
        "account_id": account_id,
        "amount": 42.5,
        "merchant": "Supermarket",
        "description": "Weekly groceries",
        "transaction_date": datetime.utcnow().isoformat(),
        "category_id": category_id,
    }
    tx_resp = client.post("/transactions/", json=payload, headers=headers)
    assert tx_resp.status_code == 200
    tx = tx_resp.json()
    tx_id = tx["id"]
    assert tx["category_id"] == category_id

    # list transactions filtered by category
    list_resp = client.get(f"/transactions/?category_id={category_id}", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == tx_id

    # get transaction by id
    get_resp = client.get(f"/transactions/{tx_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["category_id"] == category_id

    # update transaction with null should leave category unchanged (service ignores None)
    upd = client.put(
        f"/transactions/{tx_id}", json={"category_id": None}, headers=headers
    )
    assert upd.status_code == 200
    assert upd.json()["category_id"] == category_id

    # delete transaction
    del_resp = client.delete(f"/transactions/{tx_id}", headers=headers)
    assert del_resp.status_code == 200

    # verify empty list
    list_resp2 = client.get("/transactions/", headers=headers)
    assert list_resp2.status_code == 200
    assert list_resp2.json()["total"] == 0
