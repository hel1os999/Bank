"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-26 20:00:00.000000

"""

from typing import Sequence, Union

import fastapi_users_db_sqlalchemy
from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade(engine_name: str) -> None:
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name: str) -> None:
    globals()["downgrade_%s" % engine_name]()


# ──────────────────────────────────────────────
#  Engine 1 — userdata DB (users, documents, surveys)
# ──────────────────────────────────────────────

def upgrade_engine1() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "access_tokens",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=43), nullable=False),
        sa.Column(
            "created_at",
            fastapi_users_db_sqlalchemy.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_access_tokens_user_id_users"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("token", name=op.f("pk_access_tokens")),
    )
    op.create_index(
        op.f("ix_access_tokens_created_at"), "access_tokens", ["created_at"], unique=False
    )

    op.create_table(
        "user_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.String(), nullable=False),
        sa.Column("passport_number", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "verification_status",
            sa.String(),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_documents_user_id_users"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_documents")),
        sa.UniqueConstraint(
            "passport_number", name=op.f("uq_user_documents_passport_number")
        ),
    )

    op.create_table(
        "user_surveys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_document_id", sa.Integer(), nullable=False),
        sa.Column("residential_address", sa.String(), nullable=False),
        sa.Column(
            "work",
            sa.Enum(
                "DOCTOR", "EDUCATION_SECTOR", "IT", "MANAGER", "ENGINEER", "DRIVER",
                "PILOT", "FINANCE_INDUSTRY", "SALES_FIELD", "LOGISTIC_FIELD",
                "CREATIVE_FIELD", "MEDIA_FIELD", "RESEARCH_SECTOR", "STATE_STRUCTURE",
                "AGRICULTURAL_SECTOR", "UNEMPLOYED", "STUDENT", "RETIRED",
                "SELF_EMPLOYED",
                name="work",
            ),
            nullable=False,
        ),
        sa.Column(
            "work_experience",
            sa.Enum(
                "LACK_OF_EXPERIENCE", "LESS_THAN_MONTH", "FROM_ONE_TO_THREE_MONTHS",
                "FROM_THREE_TO_SIX_MONTHS", "FROM_SIX_TO_TWELVE_MONTHS",
                "FROM_ONE_TO_THREE_YEARS", "MORE_THAN_THREE_YEARS",
                name="workexperience",
            ),
            nullable=False,
        ),
        sa.Column("salary", sa.String(), nullable=False),
        sa.Column("additional_income", sa.String(), nullable=True),
        sa.Column("work_address", sa.String(), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_document_id"],
            ["user_documents.id"],
            name=op.f("fk_user_surveys_user_document_id_user_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_surveys")),
    )


def downgrade_engine1() -> None:
    op.drop_table("user_surveys")
    op.drop_table("user_documents")
    op.drop_index(op.f("ix_access_tokens_created_at"), table_name="access_tokens")
    op.drop_table("access_tokens")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")


# ──────────────────────────────────────────────
#  Engine 2 — bank DB (accounts, cards, transactions, …)
# ──────────────────────────────────────────────

def upgrade_engine2() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("user_survey_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("balance", sa.String(), nullable=False),
        sa.Column("available_balance", sa.String(), nullable=True),
        sa.Column(
            "account_type",
            sa.Enum("DEBIT", "CREDIT", "SAVINGS", name="accounttype"),
            server_default=sa.text("'CREDIT'"),
            nullable=False,
        ),
        sa.Column("IBAN", sa.String(), nullable=False),
        sa.Column(
            "currency",
            sa.Enum("USD", "EUR", name="currency"),
            server_default=sa.text("'EUR'"),
            nullable=False,
        ),
        sa.Column("limits", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
    )
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"], unique=False)

    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("CVV", sa.String(), nullable=False),
        sa.Column("full_card_number", sa.String(), nullable=False),
        sa.Column("last_four", sa.String(), nullable=False),
        sa.Column("validity_period", sa.Integer(), nullable=False),
        sa.Column(
            "card_type",
            sa.Enum("VISA", "MASTERCARD", name="cardtype"),
            nullable=False,
        ),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expiry_date", sa.DateTime(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("spending_limit", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_cards_account_id_accounts"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cards")),
        sa.UniqueConstraint("full_card_number", name=op.f("uq_cards_full_card_number")),
        sa.UniqueConstraint("last_four", name=op.f("uq_cards_last_four")),
        sa.UniqueConstraint("token", name=op.f("uq_cards_token")),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("sender_account_id", sa.Integer(), nullable=True),
        sa.Column("sender_card_id", sa.Integer(), nullable=False),
        sa.Column("receiver_card_number", sa.String(), nullable=False),
        sa.Column("receiver_card_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.String(), nullable=False),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["receiver_card_id"],
            ["cards.id"],
            name=op.f("fk_transactions_receiver_card_id_cards"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["sender_card_id"],
            ["cards.id"],
            name=op.f("fk_transactions_sender_card_id_cards"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["sender_account_id"],
            ["accounts.id"],
            name=op.f("fk_transactions_sender_account_id_accounts"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(
        op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_idempotency_key"),
        "transactions",
        ["idempotency_key"],
        unique=False,
    )

    op.create_table(
        "beneficiaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("iban", sa.String(), nullable=True),
        sa.Column("card_token", sa.String(), nullable=True),
        sa.Column(
            "currency",
            sa.String(),
            server_default=sa.text("'EUR'"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(), server_default=sa.text("'ACTIVE'"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_beneficiaries")),
    )
    op.create_index(
        op.f("ix_beneficiaries_user_id"), "beneficiaries", ["user_id"], unique=False
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("beneficiary_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.String(), nullable=False),
        sa.Column(
            "currency",
            sa.String(),
            server_default=sa.text("'EUR'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column(
            "payment_type",
            sa.String(),
            server_default=sa.text("'TRANSFER'"),
            nullable=False,
        ),
        sa.Column("counterparty_name", sa.String(), nullable=True),
        sa.Column("counterparty_iban", sa.String(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_payments_account_id_accounts"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["beneficiary_id"],
            ["beneficiaries.id"],
            name=op.f("fk_payments_beneficiary_id_beneficiaries"),
            ondelete="set null",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name=op.f("uq_payments_user_id_idempotency_key"),
        ),
    )
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False)

    op.create_table(
        "credits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("principal_amount", sa.String(), nullable=False),
        sa.Column("outstanding_amount", sa.String(), nullable=False),
        sa.Column("interest_rate", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("next_payment_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_credits_account_id_accounts"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credits")),
    )
    op.create_index(op.f("ix_credits_user_id"), "credits", ["user_id"], unique=False)

    op.create_table(
        "deposits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("principal_amount", sa.String(), nullable=False),
        sa.Column("interest_rate", sa.Float(), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("maturity_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_deposits_account_id_accounts"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deposits")),
    )
    op.create_index(op.f("ix_deposits_user_id"), "deposits", ["user_id"], unique=False)

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("entry_type", sa.String(), nullable=False),
        sa.Column("amount", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("balance_after", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_ledger_entries_account_id_accounts"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payments.id"],
            name=op.f("fk_ledger_entries_payment_id_payments"),
            ondelete="set null",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name=op.f("fk_ledger_entries_transaction_id_transactions"),
            ondelete="set null",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ledger_entries")),
    )
    op.create_index(
        op.f("ix_ledger_entries_user_id"), "ledger_entries", ["user_id"], unique=False
    )


def downgrade_engine2() -> None:
    op.drop_index(op.f("ix_ledger_entries_user_id"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index(op.f("ix_deposits_user_id"), table_name="deposits")
    op.drop_table("deposits")
    op.drop_index(op.f("ix_credits_user_id"), table_name="credits")
    op.drop_table("credits")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_beneficiaries_user_id"), table_name="beneficiaries")
    op.drop_table("beneficiaries")
    op.drop_index(op.f("ix_transactions_idempotency_key"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("cards")
    op.drop_index(op.f("ix_accounts_user_id"), table_name="accounts")
    op.drop_table("accounts")
