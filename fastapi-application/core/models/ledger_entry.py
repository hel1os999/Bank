from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BankBase


class LedgerEntry(BankBase):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.id", ondelete="cascade"),
        nullable=False,
    )
    payment_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("payments.id", ondelete="set null"),
        nullable=True,
    )
    transaction_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("transactions.id", ondelete="set null"),
        nullable=True,
    )
    entry_type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[str]
    currency: Mapped[str] = mapped_column(String, nullable=False)
    balance_after: Mapped[str]
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime]

    account = relationship("Account", back_populates="ledger_entries")
    payment = relationship("Payment", back_populates="ledger_entries")
