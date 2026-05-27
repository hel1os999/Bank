from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class UserDocumentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    passport_number: str
    data: dict


class UserDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    data: dict
    passport_number: str
    updated_at: datetime
    verification_status: str
