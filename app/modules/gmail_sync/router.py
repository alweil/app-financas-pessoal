"""Gmail sync router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.modules.auth.router import get_current_user
from app.modules.gmail_sync.schemas import (
    GmailAuthResponse,
    GmailSyncConfig,
    SyncResult,
)
from app.modules.gmail_sync.service import (
    create_auth_flow,
    delete_credentials,
    delete_oauth_state,
    get_auth_url,
    get_credentials,
    get_oauth_user,
    save_credentials,
    save_oauth_state,
    sync_gmail_emails,
)

router = APIRouter(prefix="/gmail", tags=["gmail_sync"])


@router.post("/auth/init", response_model=GmailAuthResponse)
def init_auth(current_user: User = Depends(get_current_user)):
    """Initialize Gmail OAuth flow.

    Returns authorization URL for user to complete OAuth.
    """
    try:
        flow = create_auth_flow()
        auth_url, state = get_auth_url(flow)
        save_oauth_state(state, current_user.id)
        return GmailAuthResponse(auth_url=auth_url, state=state)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create auth flow: {str(e)}"
        )


@router.get("/callback")
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle OAuth callback from Google.

    This endpoint receives the authorization code and exchanges it for tokens.
    """
    user_id = get_oauth_user(state)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        flow = create_auth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Store credentials (use secure storage in production!)
        creds_dict = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }
        save_credentials(user_id, creds_dict)
        delete_oauth_state(state)

        return {
            "status": "success",
            "message": "Gmail authentication successful! You can now sync emails.",
            "user_id": user_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to complete OAuth: {str(e)}"
        )


@router.post("/sync", response_model=SyncResult)
def sync_emails(
    account_id: int,
    config: GmailSyncConfig = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync emails from Gmail and create transactions.

    Args:
        account_id: Bank account ID to associate transactions with
        config: Sync configuration (query, max_results)
        user_id: User ID (default: 1)

    Returns:
        SyncResult with statistics
    """
    credentials = get_credentials(current_user.id)
    if not credentials:
        raise HTTPException(
            status_code=401, detail="Gmail not authenticated. Call /auth/init first."
        )

    result = sync_gmail_emails(
        db=db,
        credentials_dict=credentials,
        account_id=account_id,
        config=config,
        user_id=current_user.id,
    )

    return result


@router.get("/status")
def get_status(current_user: User = Depends(get_current_user)):
    """Check Gmail authentication status."""
    is_authenticated = bool(get_credentials(current_user.id))
    return {"authenticated": is_authenticated, "user_id": current_user.id}


@router.post("/disconnect")
def disconnect(current_user: User = Depends(get_current_user)):
    """Disconnect Gmail (remove stored credentials)."""
    delete_credentials(current_user.id)
    return {"status": "success", "message": "Gmail disconnected"}
