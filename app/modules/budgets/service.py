from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.pagination import paginate_query

from app.models import Budget, BudgetPeriod, Category, Transaction
from app.modules.budgets.schemas import BudgetCreate, BudgetSummary, BudgetUpdate


def create_budget(db: Session, user_id: int, payload: BudgetCreate) -> Budget:
    budget = Budget(
        user_id=user_id,
        category_id=payload.category_id,
        amount_limit=payload.amount_limit,
        period=BudgetPeriod(payload.period),
        start_date=payload.start_date or datetime.now(UTC),
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def list_budgets(db: Session, user_id: int, skip: int, limit: int) -> tuple[list[Budget], int]:
    query = db.query(Budget).filter(Budget.user_id == user_id)
    return paginate_query(query, skip=skip, limit=limit)


def get_budget(db: Session, user_id: int, budget_id: int) -> Budget | None:
    return db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()


def update_budget(
    db: Session,
    user_id: int,
    budget_id: int,
    payload: BudgetUpdate,
) -> Budget | None:
    budget = get_budget(db, user_id=user_id, budget_id=budget_id)
    if not budget:
        return None

    if "amount_limit" in payload.model_fields_set:
        budget.amount_limit = payload.amount_limit
    if "period" in payload.model_fields_set:
        budget.period = BudgetPeriod(payload.period)
    if "start_date" in payload.model_fields_set:
        budget.start_date = payload.start_date

    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, user_id: int, budget_id: int) -> bool:
    budget = get_budget(db, user_id=user_id, budget_id=budget_id)
    if not budget:
        return False
    db.delete(budget)
    db.commit()
    return True


def get_budget_summary(
    db: Session,
    user_id: int,
    budget_id: int,
    include_subcategories: bool,
) -> BudgetSummary | None:
    budget = get_budget(db, user_id=user_id, budget_id=budget_id)
    if not budget:
        return None

    period_start, period_end = _resolve_period_window(budget.start_date, budget.period)
    category_ids = _collect_category_ids(db, budget.category_id, include_subcategories)

    amount_spent = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.category_id.in_(category_ids))
        .filter(Transaction.transaction_date >= period_start)
        .filter(Transaction.transaction_date < period_end)
        .scalar()
    )
    amount_remaining = budget.amount_limit - amount_spent

    return BudgetSummary(
        budget_id=budget.id,
        category_id=budget.category_id,
        amount_limit=budget.amount_limit,
        amount_spent=amount_spent,
        amount_remaining=amount_remaining,
        period_start=period_start,
        period_end=period_end,
        include_subcategories=include_subcategories,
    )


def _resolve_period_window(start_date: datetime, period: BudgetPeriod) -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    if period == BudgetPeriod.weekly:
        return _rolling_window(start_date, now, days=7)
    if period == BudgetPeriod.monthly:
        return _rolling_window_months(start_date, now, months=1)
    return _rolling_window_years(start_date, now, years=1)


def _rolling_window(start_date: datetime, now: datetime, days: int) -> tuple[datetime, datetime]:
    delta_days = (now - start_date).days
    if delta_days < 0:
        return start_date, start_date + timedelta(days=days)
    periods = delta_days // days
    window_start = start_date + timedelta(days=periods * days)
    window_end = window_start + timedelta(days=days)
    return window_start, window_end


def _rolling_window_months(start_date: datetime, now: datetime, months: int) -> tuple[datetime, datetime]:
    window_start = start_date
    window_end = _add_months(window_start, months)
    while window_end <= now:
        window_start = window_end
        window_end = _add_months(window_start, months)
    return window_start, window_end


def _rolling_window_years(start_date: datetime, now: datetime, years: int) -> tuple[datetime, datetime]:
    window_start = start_date
    window_end = _add_years(window_start, years)
    while window_end <= now:
        window_start = window_end
        window_end = _add_years(window_start, years)
    return window_start, window_end


def _add_months(value: datetime, months: int) -> datetime:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, _days_in_month(year, month))
    return value.replace(year=year, month=month, day=day)


def _add_years(value: datetime, years: int) -> datetime:
    year = value.year + years
    day = min(value.day, _days_in_month(year, value.month))
    return value.replace(year=year, day=day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


def _collect_category_ids(db: Session, category_id: int, include_subcategories: bool) -> list[int]:
    if not include_subcategories:
        return [category_id]
    ids = [category_id]
    queue = [category_id]
    while queue:
        current = queue.pop(0)
        children = db.query(Category.id).filter(Category.parent_id == current).all()
        for (child_id,) in children:
            if child_id not in ids:
                ids.append(child_id)
                queue.append(child_id)
    return ids
