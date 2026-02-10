from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.modules.auth.router import get_current_user
from app.modules.email_parser.parser import parse_email
from app.modules.email_parser.schemas import (
    ParseAndCreateResponse,
    ParseToTransactionRequest,
    ParseToTransactionResponse,
    ParsedTransaction,
    RawEmailIngest,
)
from app.modules.email_parser.service import build_transaction_create, build_transaction_draft, ingest_email
from app.modules.transactions.service import create_transaction

router = APIRouter(prefix="/email", tags=["email_parser"])


@router.post("/ingest")
def ingest(
    payload: RawEmailIngest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ingest_email(db, user_id=current_user.id, payload=payload)


@router.post("/parse", response_model=ParsedTransaction)
def parse(payload: RawEmailIngest):
    return parse_email(payload)


@router.post("/parse-to-transaction", response_model=ParseToTransactionResponse)
def parse_to_transaction(payload: ParseToTransactionRequest):
    parsed = parse_email(payload.email)
    draft = build_transaction_draft(parsed, payload.account_id, payload.category_id)
    return ParseToTransactionResponse(parsed=parsed, transaction=draft)


@router.post("/parse-and-create", response_model=ParseAndCreateResponse)
def parse_and_create(
    payload: ParseToTransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parsed = parse_email(payload.email)
    if not parsed.success:
        return ParseAndCreateResponse(parsed=parsed, transaction=None)
    raw = ingest_email(db, user_id=current_user.id, payload=payload.email)
    create_payload = build_transaction_create(
        parsed,
        account_id=payload.account_id,
        category_id=payload.category_id,
        raw_email_id=raw.id,
    )
    if not create_payload:
        return ParseAndCreateResponse(parsed=parsed, transaction=None)
    try:
        transaction = create_transaction(db, user_id=current_user.id, payload=create_payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ParseAndCreateResponse(parsed=parsed, transaction=transaction)
