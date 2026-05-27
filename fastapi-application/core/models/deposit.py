from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BankBase


class Deposit(BankBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.id", ondelete="cascade"),
        nullable=False,
    )
    principal_amount: Mapped[str]
    interest_rate: Mapped[float]
    term_months: Mapped[int]
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
    )
    opened_at: Mapped[datetime]
    maturity_date: Mapped[datetime]

    account = relationship("Account", back_populates="deposits")
