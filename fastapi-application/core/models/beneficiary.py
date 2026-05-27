from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import BankBase


class Beneficiary(BankBase):
    __tablename__ = "beneficiaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str]
    iban: Mapped[str | None] = mapped_column(String, nullable=True)
    card_token: Mapped[str | None] = mapped_column(String, nullable=True)
    currency: Mapped[str] = mapped_column(
        String, nullable=False, default="EUR", server_default=text("'EUR'")
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="ACTIVE", server_default=text("'ACTIVE'")
    )
    created_at: Mapped[datetime]

    payments = relationship("Payment", back_populates="beneficiary")
