from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import Integer, ForeignKey, Enum, String, text
from sqlalchemy.orm import Mapped, relationship, mapped_column

from core.enums import CardType
from core.models import BankBase

if TYPE_CHECKING:
    from core.models import Account


class Card(BankBase):

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.id", ondelete="cascade"),
        nullable=False,
    )
    CVV: Mapped[str]
    full_card_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    last_four: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    validity_period: Mapped[int]
    card_type: Mapped[CardType] = mapped_column(Enum(CardType), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime]
    expiry_date: Mapped[datetime]
    is_blocked: Mapped[bool]
    spending_limit: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
    )

    account: Mapped["Account"] = relationship("Account", back_populates="cards")

    sent_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.sender_card_id",
        back_populates="from_card",
    )

    received_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.receiver_card_id",
        back_populates="to_card",
    )
