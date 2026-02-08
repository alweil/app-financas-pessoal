from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class GmailSyncConfig(BaseModel):
    """Configuration for Gmail sync."""
    query: str = "from:(noreply@nubank.com.br OR nubank OR itau.com.br OR bradesco OR btg OR bancointer) newer_than:1d"
    max_results: int = 50


class GmailMessage(BaseModel):
    """Represents a Gmail message."""
    id: str
    thread_id: str
    from_address: str
    subject: Optional[str] = None
    body: str
    received_at: Optional[datetime] = None
    bank_source: Optional[str] = None


class SyncResult(BaseModel):
    """Result of a sync operation."""
    messages_found: int
    messages_parsed: int
    transactions_created: int
    errors: List[str]


class GmailAuthRequest(BaseModel):
    """Request to initiate Gmail OAuth flow."""
    user_id: int = 1


class GmailAuthResponse(BaseModel):
    """Response with OAuth URL."""
    auth_url: str
    state: str


class GmailAuthCallback(BaseModel):
    """Callback from OAuth flow."""
    code: str
    state: str
    user_id: int = 1
