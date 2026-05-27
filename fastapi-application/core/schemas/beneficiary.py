from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.enums import Currency


class BeneficiaryCreate(BaseModel):
    name: str
    iban: str | None = None
    card_number: str | None = None
    currency: Currency = Currency.EUR

    @model_validator(mode="after")
    def validate_destination(self):
        if not self.iban and not self.card_number:
            raise ValueError("Either iban or card_number must be provided")
        return self


class BeneficiaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    iban: str | None = None
    card_token: str | None = None
    currency: Currency | str
    status: str
    created_at: datetime
