from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import BudgetPeriod


class BudgetCreate(BaseModel):
    category_id: int
    amount_limit: Decimal
    period: BudgetPeriod
    start_date: datetime | None = None


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

    id: int
    category_id: int
    amount_limit: Decimal
    period: BudgetPeriod
    start_date: datetime | None = None


class BudgetUpdate(BaseModel):
    amount_limit: Decimal | None = None
    period: BudgetPeriod | None = None
    start_date: datetime | None = None


class BudgetSummary(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: float})

    budget_id: int
    category_id: int
    amount_limit: Decimal
    amount_spent: Decimal
    amount_remaining: Decimal
    period_start: datetime
    period_end: datetime
    include_subcategories: bool


class BudgetListResponse(BaseModel):
    items: list[BudgetRead]
    total: int
    skip: int
    limit: int
