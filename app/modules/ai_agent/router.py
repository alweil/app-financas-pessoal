from fastapi import APIRouter

from app.modules.ai_agent.schemas import CategorizationRequest, CategorizationResponse
from app.modules.ai_agent.service import categorize_transaction

router = APIRouter(prefix="/ai", tags=["ai_agent"])


@router.post("/categorize", response_model=CategorizationResponse)
def categorize(payload: CategorizationRequest):
    return categorize_transaction(payload)
