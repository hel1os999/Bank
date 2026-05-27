from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BankBase


class Credit(BankBase):

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.id", ondelete="cascade"),
        nullable=False,
    )
    principal_amount: Mapped[str]
    outstanding_amount: Mapped[str]
    interest_rate: Mapped[float]
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
    )
    created_at: Mapped[datetime]
    next_payment_date: Mapped[datetime]

    account = relationship("Account", back_populates="credits")
