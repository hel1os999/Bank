from pydantic import BaseModel


class ProductCatalogItem(BaseModel):
    code: str
    name: str
    description: str
    category: str
    requires_kyc: bool
