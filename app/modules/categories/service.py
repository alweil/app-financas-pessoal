from sqlalchemy.orm import Session

from app.core.pagination import paginate_query
from app.models import Budget, Category, Transaction
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate
from app.seeds.categories import DEFAULT_CATEGORIES


def create_category(db: Session, user_id: int, payload: CategoryCreate) -> Category:
    category = Category(
        user_id=user_id,
        name=payload.name,
        parent_id=payload.parent_id,
        icon=payload.icon,
        color=payload.color,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def list_categories(
    db: Session, user_id: int, skip: int, limit: int
) -> tuple[list[Category], int]:
    query = db.query(Category).filter(Category.user_id == user_id)
    return paginate_query(query, skip=skip, limit=limit)


def get_category(db: Session, user_id: int, category_id: int) -> Category | None:
    return (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.id == category_id)
        .first()
    )


def update_category(
    db: Session,
    user_id: int,
    category_id: int,
    payload: CategoryUpdate,
) -> Category | None:
    category = get_category(db, user_id=user_id, category_id=category_id)
    if not category:
        return None

    if "name" in payload.model_fields_set:
        category.name = payload.name
    if "parent_id" in payload.model_fields_set:
        category.parent_id = payload.parent_id
    if "icon" in payload.model_fields_set:
        category.icon = payload.icon
    if "color" in payload.model_fields_set:
        category.color = payload.color

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, user_id: int, category_id: int) -> bool | None:
    category = get_category(db, user_id=user_id, category_id=category_id)
    if not category:
        return None

    has_children = (
        db.query(Category)
        .filter(Category.user_id == user_id, Category.parent_id == category_id)
        .first()
        is not None
    )
    if has_children:
        raise ValueError("Category has subcategories")

    in_transactions = (
        db.query(Transaction).filter(Transaction.category_id == category_id).first()
        is not None
    )
    in_budgets = (
        db.query(Budget).filter(Budget.category_id == category_id).first() is not None
    )

    if in_transactions or in_budgets:
        raise ValueError("Category in use")

    db.delete(category)
    db.commit()
    return True


def seed_default_categories(db: Session, user_id: int) -> list[Category]:
    existing = db.query(Category).filter(Category.user_id == user_id).count()
    if existing > 0:
        return db.query(Category).filter(Category.user_id == user_id).all()
    created: list[Category] = []
    for item in DEFAULT_CATEGORIES:
        parent = Category(user_id=user_id, name=item["name"])
        db.add(parent)
        db.flush()
        created.append(parent)
        for sub_name in item["subcategories"]:
            sub = Category(user_id=user_id, name=sub_name, parent_id=parent.id)
            db.add(sub)
            created.append(sub)
    db.commit()
    return created
