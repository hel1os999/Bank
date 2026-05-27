from typing import Annotated

from aio_pika.abc import AbstractRobustChannel
from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.config import settings
from core.cache.key_builder import bank_key_builder
from core.messaging.connection import get_channel
from core.messaging.producer import produce_message
from core.models import User, bank_db_helper
from core.schemas.transactions import TransactionCreate, TransactionRead
from crud.transactions import create_pending_card_transfer, get_transaction_by_id, get_transactions

router = APIRouter(
    prefix=settings.api.v1.transactions,
    tags=["Transactions"],
)


@router.post("/{sender_card_id}", response_model=TransactionRead, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(
    sender_card_id: int,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    channel: Annotated[AbstractRobustChannel, Depends(get_channel)],
    transaction: TransactionCreate,
    user: User = Depends(current_active_user),
):
    created = await create_pending_card_transfer(
        session=session, transaction=transaction, sender_card_id=sender_card_id, user=user
    )
    await produce_message(
        {"transaction_id": created["id"]},
        channel=channel,
        routing_key=settings.rmq.transactions_routing_key,
    )
    return created


@router.get("", response_model=list[TransactionRead])
@cache(
    expire=settings.cache.expire_transactions,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.transactions_list,
)
async def list_transactions(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    card_id: Annotated[int | None, Query(description="Filter by sender card")] = None,
    account_id: Annotated[int | None, Query(description="Filter by sender account")] = None,
    user: User = Depends(current_active_user),
):
    return await get_transactions(
        session=session, user=user, limit=limit, offset=offset,
        card_id=card_id, account_id=account_id,
    )


@router.get("/{transaction_id}", response_model=TransactionRead)
async def retrieve_transaction(
    transaction_id: int,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_transaction_by_id(
        session=session, transaction_id=transaction_id, user=user
    )
