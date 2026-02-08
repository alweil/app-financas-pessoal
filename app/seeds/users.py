from sqlalchemy.orm import Session

from app.models import User
from app.modules.auth.service import hash_password


def seed_admin_user(db: Session, email: str, password: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
