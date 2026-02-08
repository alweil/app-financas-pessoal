import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AccountType(str, enum.Enum):
    checking = "checking"
    savings = "savings"
    credit_card = "credit_card"
    investment = "investment"


class BudgetPeriod(str, enum.Enum):
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    accounts: Mapped[list["Account"]] = relationship(back_populates="user")
    categories: Mapped[list["Category"]] = relationship(back_populates="user")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(80), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(120))
    last_balance: Mapped[Optional[float]] = mapped_column(Float)

    user: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(40))
    color: Mapped[Optional[str]] = mapped_column(String(20))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

    user: Mapped[Optional["User"]] = relationship(back_populates="categories")
    parent: Mapped[Optional["Category"]] = relationship(remote_side="Category.id")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category")


class RawEmail(Base):
    __tablename__ = "raw_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(String)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    bank_source: Mapped[Optional[str]] = mapped_column(String(80))


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    merchant: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(255))
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    transaction_type: Mapped[Optional[str]] = mapped_column(String(40))
    payment_method: Mapped[Optional[str]] = mapped_column(String(40))
    card_last4: Mapped[Optional[str]] = mapped_column(String(4))
    installments_total: Mapped[Optional[int]] = mapped_column(Integer)
    installments_current: Mapped[Optional[int]] = mapped_column(Integer)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    raw_email_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_emails.id"))
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped["Account"] = relationship(back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    amount_limit: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[BudgetPeriod] = mapped_column(Enum(BudgetPeriod), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category"] = relationship(back_populates="budgets")
