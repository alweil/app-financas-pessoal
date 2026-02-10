from datetime import datetime

from fastapi.testclient import TestClient

from app.modules.email_parser.parser import parse_date, parse_email
from app.modules.email_parser.schemas import RawEmailIngest


def test_bradesco_purchase():
    payload = RawEmailIngest(
        message_id="bradesco-1",
        from_address="cartoes@bradesco.com.br",
        subject="Compra aprovada",
        body="Valor: R$ 12,34\nEstabelecimento: LOJA Z",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is True
    assert result.amount == 12.34
    assert result.merchant == "LOJA Z"


def test_inter_purchase():
    payload = RawEmailIngest(
        message_id="inter-1",
        from_address="cartoes@bancointer.com.br",
        subject="Compra aprovada",
        body="Compra aprovada de R$ 45,67 em LOJA W",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is True
    assert result.amount == 45.67
    assert result.merchant == "LOJA W"


def test_generic_fallback():
    payload = RawEmailIngest(
        message_id="generic-1",
        from_address="no-reply@provider.com",
        subject="Aviso",
        body="Compra em R$ 9,99",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is True
    assert result.amount == 9.99
    assert result.transaction_type == "unknown"


def test_parse_date_short_format_returns_none():
    result = parse_date("Compra em 03/02")
    assert result is None


def test_malformed_email_returns_failure():
    payload = RawEmailIngest(
        message_id="malformed-1",
        from_address="unknown@provider.com",
        subject="Hello",
        body="No recognizable content",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is False


def test_email_parse_endpoints(client: TestClient):
    payload = {
        "message_id": "router-1",
        "from_address": "todomundo@nubank.com.br",
        "subject": "Compra aprovada",
        "body": "Compra de R$ 15,00 aprovada em TESTE",
        "bank_source": None,
    }

    response = client.post("/email/parse", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

    parse_to_transaction_payload = {
        "account_id": 1,
        "category_id": 2,
        "email": payload,
    }
    response = client.post(
        "/email/parse-to-transaction", json=parse_to_transaction_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parsed"]["success"] is True
    assert data["transaction"]["amount"] == 15.0
