"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-08 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bank_name", sa.String(length=80), nullable=False),
        sa.Column(
            "account_type",
            sa.Enum(
                "checking", "savings", "credit_card", "investment", name="accounttype"
            ),
            nullable=False,
        ),
        sa.Column("nickname", sa.String(length=120), nullable=True),
        sa.Column("last_balance", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_accounts_user_id"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("icon", sa.String(length=40), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_categories_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["categories.id"], name="fk_categories_parent_id"
        ),
    )

    op.create_table(
        "raw_emails",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=255), nullable=False),
        sa.Column("from_address", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column(
            "processed", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("bank_source", sa.String(length=80), nullable=True),
        sa.UniqueConstraint("message_id", name="uq_raw_emails_message_id"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_raw_emails_user_id"
        ),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("merchant", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("transaction_date", sa.DateTime(), nullable=False),
        sa.Column("transaction_type", sa.String(length=40), nullable=True),
        sa.Column("payment_method", sa.String(length=40), nullable=True),
        sa.Column("card_last4", sa.String(length=4), nullable=True),
        sa.Column("installments_total", sa.Integer(), nullable=True),
        sa.Column("installments_current", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("raw_email_id", sa.Integer(), nullable=True),
        sa.Column(
            "is_manual", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name="fk_transactions_account_id"
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name="fk_transactions_category_id"
        ),
        sa.ForeignKeyConstraint(
            ["raw_email_id"], ["raw_emails.id"], name="fk_transactions_raw_email_id"
        ),
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount_limit", sa.Float(), nullable=False),
        sa.Column(
            "period",
            sa.Enum("weekly", "monthly", "yearly", name="budgetperiod"),
            nullable=False,
        ),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_budgets_user_id"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name="fk_budgets_category_id"
        ),
    )


def downgrade() -> None:
    op.drop_table("budgets")
    op.drop_table("transactions")
    op.drop_table("raw_emails")
    op.drop_table("categories")
    op.drop_table("accounts")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS accounttype")
    op.execute("DROP TYPE IF EXISTS budgetperiod")
