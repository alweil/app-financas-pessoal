"""Gmail sync service for automatic email processing."""

import base64
import json
import os
from typing import Any, Dict, List, Optional

import redis
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RawEmail
from app.modules.email_parser.parser import detect_bank, parse_email
from app.modules.email_parser.schemas import RawEmailIngest
from app.modules.email_parser.service import build_transaction_create, ingest_email
from app.modules.gmail_sync.schemas import GmailMessage, GmailSyncConfig, SyncResult
from app.modules.transactions.service import create_transaction

# OAuth 2.0 scopes for Gmail
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
OAUTH_STATE_PREFIX = "gmail:oauth_state:"
CREDENTIALS_PREFIX = "gmail:creds:"
OAUTH_STATE_TTL_SECONDS = 15 * 60


def get_gmail_service(credentials_dict: Optional[Dict[str, Any]] = None):
    """Get Gmail API service instance.

    Args:
        credentials_dict: Optional dict with OAuth credentials

    Returns:
        Gmail API service or None if not authenticated
    """
    creds = None

    if credentials_dict:
        creds = Credentials.from_authorized_user_info(credentials_dict, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        print(f"Error building Gmail service: {e}")
        return None


def get_redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def save_oauth_state(state: str, user_id: int) -> None:
    client = get_redis_client()
    client.setex(f"{OAUTH_STATE_PREFIX}{state}", OAUTH_STATE_TTL_SECONDS, str(user_id))


def get_oauth_user(state: str) -> Optional[int]:
    client = get_redis_client()
    value = client.get(f"{OAUTH_STATE_PREFIX}{state}")
    if not value:
        return None
    return int(value)


def delete_oauth_state(state: str) -> None:
    client = get_redis_client()
    client.delete(f"{OAUTH_STATE_PREFIX}{state}")


def save_credentials(user_id: int, creds_dict: Dict[str, Any]) -> None:
    client = get_redis_client()
    client.set(f"{CREDENTIALS_PREFIX}{user_id}", json.dumps(creds_dict))


def get_credentials(user_id: int) -> Optional[Dict[str, Any]]:
    client = get_redis_client()
    value = client.get(f"{CREDENTIALS_PREFIX}{user_id}")
    if not value:
        return None
    return json.loads(value)


def delete_credentials(user_id: int) -> None:
    client = get_redis_client()
    client.delete(f"{CREDENTIALS_PREFIX}{user_id}")


def create_auth_flow(redirect_uri: Optional[str] = None) -> Flow:
    """Create OAuth2 flow for Gmail authentication.

    Returns:
        Flow instance
    """
    # In production, these should be loaded from environment or credentials.json
    client_config = {
        "web": {
            "client_id": os.getenv("GMAIL_CLIENT_ID", ""),
            "project_id": os.getenv("GMAIL_PROJECT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("GMAIL_CLIENT_SECRET", ""),
            "redirect_uris": [
                redirect_uri
                or os.getenv(
                    "GMAIL_REDIRECT_URI", "http://localhost:8000/api/v1/gmail/callback"
                )
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
        or os.getenv(
            "GMAIL_REDIRECT_URI", "http://localhost:8000/api/v1/gmail/callback"
        ),
    )
    return flow


def get_auth_url(flow: Flow) -> str:
    """Get authorization URL for OAuth flow.

    Args:
        flow: OAuth flow instance

    Returns:
        Authorization URL
    """
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return auth_url, state


def fetch_message_content(service, message_id: str) -> Optional[GmailMessage]:
    """Fetch full content of a Gmail message.

    Args:
        service: Gmail API service
        message_id: Message ID

    Returns:
        GmailMessage or None if error
    """
    try:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        # Extract headers
        headers = msg["payload"]["headers"]
        from_address = ""
        subject = ""
        date_str = ""

        for header in headers:
            if header["name"].lower() == "from":
                from_address = header["value"]
            elif header["name"].lower() == "subject":
                subject = header["value"]
            elif header["name"].lower() == "date":
                date_str = header["value"]

        # Extract body
        body = ""
        if "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode(
                            "utf-8", errors="ignore"
                        )
                        break
                elif part["mimeType"] == "text/html" and not body:
                    data = part["body"].get("data", "")
                    if data:
                        import re

                        html = base64.urlsafe_b64decode(data).decode(
                            "utf-8", errors="ignore"
                        )
                        # Simple HTML to text
                        body = re.sub("<[^<]+?>", "", html)
        else:
            data = msg["payload"]["body"].get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        # Parse date
        received_at = None
        if date_str:
            try:
                from email.utils import parsedate_to_datetime

                received_at = parsedate_to_datetime(date_str)
            except Exception:
                pass

        # Detect bank
        bank_source = detect_bank(from_address, subject)

        return GmailMessage(
            id=message_id,
            thread_id=msg["threadId"],
            from_address=from_address,
            subject=subject,
            body=body,
            received_at=received_at,
            bank_source=bank_source,
        )
    except Exception as e:
        print(f"Error fetching message {message_id}: {e}")
        return None


def search_messages(service, query: str = "", max_results: int = 50) -> List[str]:
    """Search Gmail messages by query.

    Args:
        service: Gmail API service
        query: Gmail search query
        max_results: Maximum results to return

    Returns:
        List of message IDs
    """
    try:
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        return [msg["id"] for msg in messages]
    except Exception as e:
        print(f"Error searching messages: {e}")
        return []


def sync_gmail_emails(
    db: Session,
    credentials_dict: Dict[str, Any],
    account_id: int,
    config: GmailSyncConfig,
    user_id: int = 1,
) -> SyncResult:
    """Sync Gmail emails and create transactions.

    Args:
        db: Database session
        credentials_dict: OAuth credentials
        account_id: Bank account ID to associate transactions
        config: Sync configuration
        user_id: User ID

    Returns:
        SyncResult with statistics
    """
    service = get_gmail_service(credentials_dict)
    if not service:
        return SyncResult(
            messages_found=0,
            messages_parsed=0,
            transactions_created=0,
            errors=["Failed to authenticate with Gmail"],
        )

    errors = []
    messages_found = 0
    messages_parsed = 0
    transactions_created = 0

    try:
        # Search for bank emails
        message_ids = search_messages(service, config.query, config.max_results)
        messages_found = len(message_ids)

        for msg_id in message_ids:
            # Fetch message content
            gmail_msg = fetch_message_content(service, msg_id)
            if not gmail_msg:
                continue

            # Skip if not from a bank
            if not gmail_msg.bank_source:
                continue

            # Skip if already ingested
            existing = db.query(RawEmail).filter(RawEmail.message_id == msg_id).first()
            if existing:
                continue

            # Create ingest payload
            ingest_payload = RawEmailIngest(
                message_id=msg_id,
                from_address=gmail_msg.from_address,
                subject=gmail_msg.subject,
                body=gmail_msg.body,
                bank_source=gmail_msg.bank_source,
            )

            # Parse email
            parsed = parse_email(ingest_payload)
            messages_parsed += 1

            if not parsed.success:
                continue

            # Ingest raw email
            raw = ingest_email(db, user_id=user_id, payload=ingest_payload)

            # Create transaction
            create_payload = build_transaction_create(
                parsed, account_id=account_id, category_id=None, raw_email_id=raw.id
            )

            if create_payload:
                try:
                    create_transaction(db, user_id=user_id, payload=create_payload)
                    transactions_created += 1
                except ValueError as exc:
                    errors.append(str(exc))

    except Exception as e:
        errors.append(str(e))

    return SyncResult(
        messages_found=messages_found,
        messages_parsed=messages_parsed,
        transactions_created=transactions_created,
        errors=errors,
    )
