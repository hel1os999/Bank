from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BankBase


class Payment(BankBase):
    __table_args__ = (
        UniqueConstraint(
            "user_id", "idempotency_key", name="uq_payments_user_id_idempotency_key"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.id", ondelete="cascade"),
        nullable=False,
    )
    beneficiary_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("beneficiaries.id", ondelete="set null"),
        nullable=True,
    )
    amount: Mapped[str]
    currency: Mapped[str] = mapped_column(
        String, nullable=False, default="EUR", server_default=text("'EUR'")
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="PENDING", server_default=text("'PENDING'")
    )
    payment_type: Mapped[str] = mapped_column(
        String, nullable=False, default="TRANSFER", server_default=text("'TRANSFER'")
    )
    counterparty_name: Mapped[str | None] = mapped_column(String, nullable=True)
    counterparty_iban: Mapped[str | None] = mapped_column(String, nullable=True)
    reference: Mapped[str | None] = mapped_column(String, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    account = relationship("Account", back_populates="payments")
    beneficiary = relationship("Beneficiary", back_populates="payments")
    ledger_entries = relationship("LedgerEntry", back_populates="payment")
