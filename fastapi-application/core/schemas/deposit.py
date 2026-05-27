from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DepositCreate(BaseModel):
    principal_amount: Decimal = Field(gt=0)
    interest_rate: float = Field(default=4.0, ge=0)
    term_months: int = Field(default=12, gt=0)


class DepositRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    principal_amount: Decimal
    interest_rate: float
    term_months: int
    status: str
    opened_at: datetime
    maturity_date: datetime
