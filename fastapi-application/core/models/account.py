from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import text, Enum, String
from sqlalchemy.orm import Mapped, relationship, mapped_column

from core.enums import AccountType, Currency
from core.models import BankBase


if TYPE_CHECKING:
    from core.models import Card, Credit, Deposit, LedgerEntry, Payment


class Account(BankBase):

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    user_survey_id: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime]
    balance: Mapped[str]
    available_balance: Mapped[str]
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType),
        default=AccountType.CREDIT,
        server_default=text("'CREDIT'"),  # only caps, only CREDIT or DEBIT
        nullable=False,
    )
    IBAN: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency),
        default=Currency.EUR,
        server_default=text("'EUR'"),
        nullable=False,
    )
    limits: Mapped[str]
    status: Mapped[str] = mapped_column(
        nullable=False,
        default="active",
        server_default=text("'ACTIVE'"),
    )

    cards: Mapped[list["Card"]] = relationship("Card", back_populates="account")
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="account"
    )
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(
        "LedgerEntry", back_populates="account"
    )
    credits: Mapped[list["Credit"]] = relationship("Credit", back_populates="account")
    deposits: Mapped[list["Deposit"]] = relationship(
        "Deposit", back_populates="account"
    )
