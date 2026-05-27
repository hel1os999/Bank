from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, String, text
from sqlalchemy.orm import Mapped, relationship, mapped_column

from core.models import BankBase

if TYPE_CHECKING:
    from core.models import Account


class Transaction(BankBase):

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    sender_account_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("accounts.id", ondelete="cascade"),
        nullable=True,
    )

    sender_card_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cards.id", ondelete="cascade"),
        nullable=False,
    )
    receiver_card_number: Mapped[str]
    receiver_card_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cards.id", ondelete="cascade"),
        nullable=False,
    )
    amount: Mapped[str]
    transaction_type: Mapped[str]
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    reference: Mapped[str | None] = mapped_column(nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(nullable=True)
    timestamp: Mapped[datetime]

    from_card = relationship(
        "Card", foreign_keys=[sender_card_id], back_populates="sent_transactions"
    )

    to_card = relationship(
        "Card", foreign_keys=[receiver_card_id], back_populates="received_transactions"
    )
