"""Gmail sync router for API endpoints."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.gmail_sync.schemas import (
    GmailAuthRequest,
    GmailAuthResponse,
    GmailAuthCallback,
    GmailSyncConfig,
    SyncResult
)
from app.modules.gmail_sync.service import (
    create_auth_flow,
    get_auth_url,
    sync_gmail_emails
)

router = APIRouter(prefix="/gmail", tags=["gmail_sync"])

# Temporary storage for OAuth states (use Redis in production)
oauth_states: Dict[str, int] = {}
# Temporary storage for credentials (use database in production)
stored_credentials: Dict[int, Dict[str, Any]] = {}


@router.post("/auth/init", response_model=GmailAuthResponse)
def init_auth(request: GmailAuthRequest):
    """Initialize Gmail OAuth flow.
    
    Returns authorization URL for user to complete OAuth.
    """
    try:
        flow = create_auth_flow()
        auth_url, state = get_auth_url(flow)
        oauth_states[state] = request.user_id
        return GmailAuthResponse(auth_url=auth_url, state=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create auth flow: {str(e)}")


@router.get("/callback")
def oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Google.
    
    This endpoint receives the authorization code and exchanges it for tokens.
    """
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    user_id = oauth_states[state]
    
    try:
        flow = create_auth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials (use secure storage in production!)
        creds_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        stored_credentials[user_id] = creds_dict
        
        return {
            "status": "success",
            "message": "Gmail authentication successful! You can now sync emails.",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth: {str(e)}")


@router.post("/sync", response_model=SyncResult)
def sync_emails(
    account_id: int,
    config: GmailSyncConfig = Depends(),
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """Sync emails from Gmail and create transactions.
    
    Args:
        account_id: Bank account ID to associate transactions with
        config: Sync configuration (query, max_results)
        user_id: User ID (default: 1)
        
    Returns:
        SyncResult with statistics
    """
    if user_id not in stored_credentials:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Call /auth/init first."
        )
    
    credentials = stored_credentials[user_id]
    
    result = sync_gmail_emails(
        db=db,
        credentials_dict=credentials,
        account_id=account_id,
        config=config,
        user_id=user_id
    )
    
    return result


@router.get("/status")
def get_status(user_id: int = 1):
    """Check Gmail authentication status."""
    is_authenticated = user_id in stored_credentials
    return {
        "authenticated": is_authenticated,
        "user_id": user_id
    }


@router.post("/disconnect")
def disconnect(user_id: int = 1):
    """Disconnect Gmail (remove stored credentials)."""
    if user_id in stored_credentials:
        del stored_credentials[user_id]
    return {"status": "success", "message": "Gmail disconnected"}
