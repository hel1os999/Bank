from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from core.enums import Currency, LedgerEntryType


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    payment_id: int | None = None
    transaction_id: int | None = None
    entry_type: LedgerEntryType | str
    amount: Decimal
    currency: Currency | str
    balance_after: Decimal
    description: str | None = None
    created_at: datetime
