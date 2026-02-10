from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models import RawEmail
from app.modules.email_parser.schemas import ParsedTransaction, RawEmailIngest
from app.modules.gmail_sync.schemas import GmailMessage, GmailSyncConfig
from app.modules.gmail_sync.service import sync_gmail_emails


def test_sync_gmail_emails_creates_transactions(db_session):
    config = GmailSyncConfig(query="", max_results=10)

    message_ids = ["msg-1", "msg-2"]
    gmail_messages = [
        GmailMessage(
            id="msg-1",
            thread_id="t1",
            from_address="no-reply@nubank.com.br",
            subject="Compra aprovada",
            body="Compra de R$ 10,00 aprovada em TESTE",
            bank_source="nubank",
        ),
        GmailMessage(
            id="msg-2",
            thread_id="t2",
            from_address="no-reply@nubank.com.br",
            subject="Compra aprovada",
            body="Compra de R$ 20,00 aprovada em TESTE",
            bank_source="nubank",
        ),
    ]

    parsed = ParsedTransaction(
        success=True,
        bank_source="nubank",
        amount=10.0,
        merchant="TESTE",
        transaction_type="purchase",
        payment_method="credit_card",
        card_last4=None,
        installments_total=None,
        installments_current=None,
        transaction_date=None,
        description=None,
        subject=None,
        reason="test",
    )

    with (
        patch(
            "app.modules.gmail_sync.service.get_gmail_service", return_value=MagicMock()
        ),
        patch(
            "app.modules.gmail_sync.service.search_messages", return_value=message_ids
        ),
        patch(
            "app.modules.gmail_sync.service.fetch_message_content",
            side_effect=gmail_messages,
        ),
        patch("app.modules.gmail_sync.service.parse_email", return_value=parsed),
        patch(
            "app.modules.gmail_sync.service.ingest_email",
            return_value=SimpleNamespace(id=1),
        ),
        patch(
            "app.modules.gmail_sync.service.create_transaction"
        ) as create_transaction,
    ):
        result = sync_gmail_emails(
            db=db_session,
            credentials_dict={"token": "x"},
            account_id=1,
            config=config,
            user_id=1,
        )

    assert result.messages_found == 2
    assert result.messages_parsed == 2
    assert result.transactions_created == 2
    assert create_transaction.call_count == 2


def test_sync_gmail_emails_skips_non_bank(db_session):
    config = GmailSyncConfig(query="", max_results=10)

    with (
        patch(
            "app.modules.gmail_sync.service.get_gmail_service", return_value=MagicMock()
        ),
        patch("app.modules.gmail_sync.service.search_messages", return_value=["msg-1"]),
        patch(
            "app.modules.gmail_sync.service.fetch_message_content",
            return_value=GmailMessage(
                id="msg-1",
                thread_id="t1",
                from_address="no-reply@provider.com",
                subject="Aviso",
                body="Hello",
                bank_source=None,
            ),
        ),
        patch("app.modules.gmail_sync.service.parse_email") as parse_email,
    ):
        result = sync_gmail_emails(
            db=db_session,
            credentials_dict={"token": "x"},
            account_id=1,
            config=config,
            user_id=1,
        )

    assert result.messages_found == 1
    assert result.messages_parsed == 0
    assert result.transactions_created == 0
    parse_email.assert_not_called()


def test_sync_gmail_emails_deduplicates(db_session):
    existing = RawEmail(
        user_id=1,
        message_id="msg-1",
        from_address="no-reply@nubank.com.br",
        subject="Compra aprovada",
        body="Compra de R$ 10,00 aprovada em TESTE",
        bank_source="nubank",
    )
    db_session.add(existing)
    db_session.commit()

    config = GmailSyncConfig(query="", max_results=10)

    with (
        patch(
            "app.modules.gmail_sync.service.get_gmail_service", return_value=MagicMock()
        ),
        patch("app.modules.gmail_sync.service.search_messages", return_value=["msg-1"]),
        patch(
            "app.modules.gmail_sync.service.fetch_message_content",
            return_value=GmailMessage(
                id="msg-1",
                thread_id="t1",
                from_address="no-reply@nubank.com.br",
                subject="Compra aprovada",
                body="Compra de R$ 10,00 aprovada em TESTE",
                bank_source="nubank",
            ),
        ),
        patch("app.modules.gmail_sync.service.parse_email") as parse_email,
    ):
        result = sync_gmail_emails(
            db=db_session,
            credentials_dict={"token": "x"},
            account_id=1,
            config=config,
            user_id=1,
        )

    assert result.messages_found == 1
    assert result.messages_parsed == 0
    assert result.transactions_created == 0
    parse_email.assert_not_called()


def test_oauth_state_roundtrip(monkeypatch):
    from app.modules.gmail_sync import service

    store = {}

    class FakeRedis:
        def setex(self, key, _ttl, value):
            store[key] = value

        def get(self, key):
            return store.get(key)

        def delete(self, key):
            store.pop(key, None)

    monkeypatch.setattr(service, "get_redis_client", lambda: FakeRedis())

    service.save_oauth_state("state-1", 42)
    assert service.get_oauth_user("state-1") == 42
    service.delete_oauth_state("state-1")
    assert service.get_oauth_user("state-1") is None
