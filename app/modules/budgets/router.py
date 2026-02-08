from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from fastapi import HTTPException

from app.models import User
from app.modules.auth.router import get_current_user
from app.modules.budgets.schemas import BudgetCreate, BudgetRead, BudgetSummary
from app.modules.budgets.service import create_budget, get_budget_summary, list_budgets

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("/", response_model=BudgetRead)
def create(
    payload: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_budget(db, user_id=current_user.id, payload=payload)


@router.get("/", response_model=list[BudgetRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_budgets(db, user_id=current_user.id)


@router.get("/{budget_id}/summary", response_model=BudgetSummary)
def summary(
    budget_id: int,
    include_subcategories: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_budget_summary(
        db,
        user_id=current_user.id,
        budget_id=budget_id,
        include_subcategories=include_subcategories,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Budget not found")
    return result
