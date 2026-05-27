from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.config import settings
from core.cache.key_builder import bank_key_builder
from core.models import User, bank_db_helper
from core.schemas.ledger import LedgerEntryRead
from crud.ledger import get_ledger

router = APIRouter(
    prefix=settings.api.v1.ledger,
    tags=["Ledger"],
)


@router.get("", response_model=list[LedgerEntryRead])
@cache(
    expire=settings.cache.expire_ledger,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.ledger_list,
)
async def list_ledger(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    account_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    user: User = Depends(current_active_user),
):
    return await get_ledger(
        session=session, user=user, account_id=account_id, limit=limit, offset=offset
    )
