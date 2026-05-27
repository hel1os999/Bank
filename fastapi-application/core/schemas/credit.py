from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreditCreate(BaseModel):
    principal_amount: Decimal = Field(gt=0)
    interest_rate: float = Field(default=12.5, ge=0)


class CreditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    principal_amount: Decimal
    outstanding_amount: Decimal
    created_at: datetime
    next_payment_date: datetime
    interest_rate: float
    status: str
