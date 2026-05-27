from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from core.enums import AccountStatus, AccountType, Currency


class AccountCreate(BaseModel):
    account_type: AccountType = AccountType.DEBIT
    balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: Currency = Currency.EUR
    limits: Decimal = Field(
        default=Decimal("5000.00"),
        max_digits=15,
        decimal_places=2,
        ge=0,
    )


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    user_survey_id: int | None = None
    balance: Decimal
    available_balance: Decimal
    account_type: AccountType
    currency: Currency
    limits: Decimal
    IBAN: str
    status: AccountStatus | str


class AccountStatusUpdate(BaseModel):
    status: AccountStatus
