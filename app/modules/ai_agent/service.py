from sqlalchemy.orm import Session

from app.models import Category
from app.modules.ai_agent.rules import RULES, normalize
from app.modules.ai_agent.schemas import CategorizationRequest, CategorizationResponse


def categorize_transaction(payload: CategorizationRequest) -> CategorizationResponse:
    text = normalize(f"{payload.merchant or ''} {payload.description or ''}")
    for rule in RULES:
        for keyword in rule.keywords:
            normalized_keyword = normalize(keyword)
            if normalized_keyword and normalized_keyword in text:
                return CategorizationResponse(
                    category_id=None,
                    category_name=rule.category,
                    subcategory_name=rule.subcategory,
                    reason=f"Regra por palavra-chave: {keyword}",
                )
    return CategorizationResponse(
        category_id=None,
        category_name="Outros",
        subcategory_name="Outros",
        reason="Sem correspondência",
    )


def _find_category(
    categories: list[Category],
    name: str,
    parent_id: int | None = None,
) -> Category | None:
    target = normalize(name)
    for category in categories:
        if parent_id is None:
            if category.parent_id is not None:
                continue
        else:
            if category.parent_id != parent_id:
                continue
        if normalize(category.name) == target:
            return category
    return None


def categorize_with_db(
    db: Session,
    user_id: int,
    merchant: str | None,
    description: str | None,
) -> CategorizationResponse:
    response = categorize_transaction(CategorizationRequest(merchant=merchant, description=description))
    if not response.category_name:
        return response

    categories = db.query(Category).filter(Category.user_id == user_id).all()
    parent = _find_category(categories, response.category_name, parent_id=None)

    if not parent and response.category_name == "Outros":
        parent = Category(user_id=user_id, name="Outros")
        db.add(parent)
        db.commit()
        db.refresh(parent)
        categories.append(parent)

    selected = parent
    if response.subcategory_name and parent:
        child = _find_category(categories, response.subcategory_name, parent_id=parent.id)
        if not child and response.subcategory_name == "Outros":
            child = Category(user_id=user_id, name="Outros", parent_id=parent.id)
            db.add(child)
            db.commit()
            db.refresh(child)
            categories.append(child)
        if child:
            selected = child

    response.category_id = selected.id if selected else None
    return response
