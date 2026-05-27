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
from core.schemas.payment import PaymentCreate, PaymentRead
from crud.payments import create_payment, get_payment_by_id, get_payments

router = APIRouter(
    prefix=settings.api.v1.payments,
    tags=["Payments"],
)


@router.post("", response_model=PaymentRead, status_code=status.HTTP_202_ACCEPTED)
async def create_new_payment(
    payment: PaymentCreate,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    channel: Annotated[AbstractRobustChannel, Depends(get_channel)],
    user: User = Depends(current_active_user),
):
    created = await create_payment(session=session, payment=payment, user=user)
    if created["status"] == "PENDING":
        await produce_message(
            {"payment_id": created["id"]},
            channel=channel,
            routing_key=settings.rmq.payments_routing_key,
        )
    return created


@router.get("", response_model=list[PaymentRead])
@cache(
    expire=settings.cache.expire_payments,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.payments_list,
)
async def list_payments(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    user: User = Depends(current_active_user),
):
    return await get_payments(session=session, user=user, limit=limit, offset=offset)


@router.get("/{payment_id}", response_model=PaymentRead)
async def retrieve_payment(
    payment_id: int,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_payment_by_id(session=session, payment_id=payment_id, user=user)
