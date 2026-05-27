from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from core.enums import CardStatus, CardType


class CardCreate(BaseModel):
    card_type: CardType = CardType.VISA
    spending_limit: Decimal = Field(default=Decimal("1000.00"), ge=0)


class CardSpendingLimitUpdate(BaseModel):
    spending_limit: Decimal = Field(ge=0)


class CardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    masked_pan: str
    last_four: str
    validity_period: int
    card_type: CardType
    spending_limit: Decimal
    token: str
    created_at: datetime
    expiry_date: datetime
    is_blocked: bool
    status: CardStatus | str


class CardReveal(BaseModel):
    full_pan: str
    cvv: str
    expiry_date: datetime


class CardStatusUpdate(BaseModel):
    status: CardStatus
