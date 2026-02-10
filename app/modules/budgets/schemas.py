from datetime import datetime

from pydantic import BaseModel

from app.models import BudgetPeriod


class BudgetCreate(BaseModel):
    category_id: int
    amount_limit: float
    period: BudgetPeriod
    start_date: datetime | None = None


class BudgetRead(BaseModel):
    id: int
    category_id: int
    amount_limit: float
    period: BudgetPeriod
    start_date: datetime | None = None

    class Config:
        from_attributes = True


class BudgetUpdate(BaseModel):
    amount_limit: float | None = None
    period: BudgetPeriod | None = None
    start_date: datetime | None = None


class BudgetSummary(BaseModel):
    budget_id: int
    category_id: int
    amount_limit: float
    amount_spent: float
    amount_remaining: float
    period_start: datetime
    period_end: datetime
    include_subcategories: bool


class BudgetListResponse(BaseModel):
    items: list[BudgetRead]
    total: int
    skip: int
    limit: int
