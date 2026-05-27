from pydantic import BaseModel


class CustomerProfileRead(BaseModel):
    user_id: int
    email: str
    document_status: str | None = None
    survey_status: str | None = None
    kyc_status: str
    accounts_count: int
    cards_count: int
    available_products: list[str]
