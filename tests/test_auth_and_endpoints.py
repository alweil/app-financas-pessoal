from app.modules.email_parser.schemas import RawEmailIngest
from app.modules.email_parser.service import ingest_email


def register_and_login(client):
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
    return token


def test_auth_required_for_accounts(client):
    response = client.get("/accounts/")
    assert response.status_code == 401


def test_create_and_list_accounts(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/accounts/",
        json={"bank_name": "Nubank", "account_type": "checking"},
        headers=headers,
    )
    assert create_response.status_code == 200

    list_response = client.get("/accounts/", headers=headers)
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 1
    assert data["skip"] == 0
    assert data["limit"] == 50
    assert len(data["items"]) == 1
    assert data["items"][0]["bank_name"] == "Nubank"


def test_list_accounts_pagination(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    for bank_name in ["Nubank", "Inter", "Itau"]:
        response = client.post(
            "/accounts/",
            json={"bank_name": bank_name, "account_type": "checking"},
            headers=headers,
        )
        assert response.status_code == 200

    list_response = client.get("/accounts/?skip=1&limit=1", headers=headers)
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 3
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert len(data["items"]) == 1


def test_email_ingest_dedup(db_session):
    payload = RawEmailIngest(
        message_id="dup-1",
        from_address="todomundo@nubank.com.br",
        subject="Compra aprovada",
        body="Compra de R$ 10,00 aprovada em TESTE",
        bank_source=None,
    )
    first = ingest_email(db_session, user_id=1, payload=payload)
    second = ingest_email(db_session, user_id=1, payload=payload)
    assert first.id == second.id
