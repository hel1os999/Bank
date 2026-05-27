from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.catalog import get_product_catalog
from core.config import settings
from core.cache.key_builder import bank_key_builder
from core.models import User, bank_db_helper
from core.schemas.catalog import ProductCatalogItem
from core.schemas.credit import CreditCreate, CreditRead
from core.schemas.deposit import DepositCreate, DepositRead
from crud.products import (
    create_credit,
    create_deposit,
    get_credit_by_id,
    get_credits,
    get_deposit_by_id,
    get_deposits,
)

router = APIRouter(
    prefix=settings.api.v1.products,
    tags=["Products"],
)


@router.get("/catalog", response_model=list[ProductCatalogItem])
async def list_product_catalog():
    return get_product_catalog()


@router.post(
    "/accounts/{account_id}/credits",
    response_model=CreditRead,
    status_code=status.HTTP_201_CREATED,
)
async def open_credit(
    account_id: int,
    credit: CreditCreate,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await create_credit(session=session, credit=credit, account_id=account_id, user=user)


@router.get("/credits", response_model=list[CreditRead])
@cache(
    expire=settings.cache.expire_credits,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.credits_list,
)
async def list_credits(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    user: User = Depends(current_active_user),
):
    return await get_credits(session=session, user=user, limit=limit, offset=offset)


@router.get("/credits/{credit_id}", response_model=CreditRead)
async def retrieve_credit(
    credit_id: int,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_credit_by_id(session=session, credit_id=credit_id, user=user)


@router.post(
    "/accounts/{account_id}/deposits",
    response_model=DepositRead,
    status_code=status.HTTP_201_CREATED,
)
async def open_deposit(
    account_id: int,
    deposit: DepositCreate,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await create_deposit(session=session, deposit=deposit, account_id=account_id, user=user)


@router.get("/deposits", response_model=list[DepositRead])
@cache(
    expire=settings.cache.expire_deposits,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.deposits_list,
)
async def list_deposits(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    user: User = Depends(current_active_user),
):
    return await get_deposits(session=session, user=user, limit=limit, offset=offset)


@router.get("/deposits/{deposit_id}", response_model=DepositRead)
async def retrieve_deposit(
    deposit_id: int,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_deposit_by_id(session=session, deposit_id=deposit_id, user=user)
