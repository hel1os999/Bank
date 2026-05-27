from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    receiver_card_number: str
    amount: Decimal = Field(gt=0)
    transaction_type: str = "CARD_TRANSFER"
    idempotency_key: str | None = None
    reference: str | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    sender_card_id: int
    receiver_card_id: int
    sender_account_id: int | None = None
    receiver_card_number: str
    amount: Decimal
    transaction_type: str
    status: str
    idempotency_key: str | None = None
    reference: str | None = None
    failure_reason: str | None = None
    timestamp: datetime
