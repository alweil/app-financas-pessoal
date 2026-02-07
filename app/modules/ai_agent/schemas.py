from pydantic import BaseModel


class CategorizationRequest(BaseModel):
    merchant: str | None = None
    description: str | None = None


class CategorizationResponse(BaseModel):
    category_id: int | None = None
    category_name: str | None = None
    subcategory_name: str | None = None
    reason: str | None = None
