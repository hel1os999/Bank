from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from core.enums import Currency, PaymentStatus


class PaymentCreate(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0)
    currency: Currency = Currency.EUR
    idempotency_key: str = Field(min_length=8, max_length=128)
    beneficiary_id: int | None = None
    counterparty_name: str | None = None
    counterparty_iban: str | None = None
    reference: str | None = None
    payment_type: str = "TRANSFER"


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    beneficiary_id: int | None = None
    amount: Decimal
    currency: Currency | str
    status: PaymentStatus | str
    payment_type: str
    counterparty_name: str | None = None
    counterparty_iban: str | None = None
    reference: str | None = None
    idempotency_key: str
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
