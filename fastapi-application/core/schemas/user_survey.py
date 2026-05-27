from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UserSurveyCreate(BaseModel):
    residential_address: str
    work: str
    work_experience: str
    salary: Decimal = Field(ge=0)
    additional_income: Decimal | None = Field(ge=0)
    work_address: str | None


class UserSurveyRead(UserSurveyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_document_id: int
    verification_status: str
