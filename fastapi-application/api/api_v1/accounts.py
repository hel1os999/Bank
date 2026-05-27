from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.config import settings
from core.cache.key_builder import bank_key_builder
from core.models import bank_db_helper, User, userdata_db_helper
from core.schemas.account import AccountCreate, AccountRead, AccountStatusUpdate
from crud.accounts import (
    create_account,
    get_account_by_id,
    get_accounts,
    update_account_status,
)

router = APIRouter(
    prefix=settings.api.v1.accounts,
    tags=["Accounts"],
)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_accounts(
    account: AccountCreate,
    user_session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    bank_session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await create_account(
        account=account, user_session=user_session, bank_session=bank_session, user=user
    )


@router.get("", response_model=list[AccountRead])
@cache(
    expire=settings.cache.expire_accounts,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.accounts_list,
)
async def list_accounts(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    limit: Annotated[int, Query(ge=1, le=100, description="Max records per page")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    user: User = Depends(current_active_user),
):
    return await get_accounts(session=session, user=user, limit=limit, offset=offset)


@router.get("/{account_id}", response_model=AccountRead)
@cache(
    expire=settings.cache.expire_accounts,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.accounts_detail,
)
async def retrieve_account(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    account_id: int,
    user: User = Depends(current_active_user),
):
    return await get_account_by_id(session=session, account_id=account_id, user=user)


@router.patch("/{account_id}/status", response_model=AccountRead)
async def change_account_status(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    account_id: int,
    payload: AccountStatusUpdate,
    user: User = Depends(current_active_user),
):
    return await update_account_status(
        session=session,
        account_id=account_id,
        user=user,
        status_value=payload.status.value,
    )
