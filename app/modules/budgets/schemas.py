from datetime import datetime

from pydantic import BaseModel


class BudgetCreate(BaseModel):
    category_id: int
    amount_limit: float
    period: str
    start_date: datetime | None = None


class BudgetRead(BaseModel):
    id: int
    category_id: int
    amount_limit: float
    period: str
    start_date: datetime | None = None

    class Config:
        from_attributes = True


class BudgetSummary(BaseModel):
    budget_id: int
    category_id: int
    amount_limit: float
    amount_spent: float
    amount_remaining: float
    period_start: datetime
    period_end: datetime
    include_subcategories: bool
