from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.config import settings
from core.cache.key_builder import bank_key_builder
from core.models import User, bank_db_helper, userdata_db_helper
from core.schemas.card import CardCreate, CardRead, CardReveal, CardSpendingLimitUpdate, CardStatusUpdate
from crud.cards import (
    create_card,
    get_card_by_id,
    get_cards,
    get_reveal_card_by_id,
    update_card_status,
    update_spending_limit,
)

router = APIRouter(
    prefix=settings.api.v1.cards,
    tags=["Cards"],
)


@router.post("/{account_id}", response_model=CardRead, status_code=status.HTTP_201_CREATED)
async def create_cards(
    account_id: int,
    card: CardCreate,
    user_session: Annotated[AsyncSession, Depends(userdata_db_helper.session_getter)],
    bank_session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await create_card(
        card=card,
        account_id=account_id,
        user_session=user_session,
        bank_session=bank_session,
        user=user,
    )


@router.get("", response_model=list[CardRead])
@cache(
    expire=settings.cache.expire_cards,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.cards_list,
)
async def list_cards(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    user: User = Depends(current_active_user),
):
    return await get_cards(session=session, user=user, limit=limit, offset=offset)


@router.get("/{card_id}", response_model=CardRead)
@cache(
    expire=settings.cache.expire_cards,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.cards_detail,
)
async def retrieve_card(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    card_id: int,
    user: User = Depends(current_active_user),
):
    return await get_card_by_id(session=session, card_id=card_id, user=user)


@router.get("/{card_id}/reveal", response_model=CardReveal)
async def get_reveal_cards_by_id(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    card_id: int,
    user: User = Depends(current_active_user),
):
    return await get_reveal_card_by_id(session=session, card_id=card_id, user=user)


@router.patch("/{card_id}/status", response_model=CardRead)
async def change_card_status(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    card_id: int,
    payload: CardStatusUpdate,
    user: User = Depends(current_active_user),
):
    return await update_card_status(
        session=session, card_id=card_id, user=user, status_value=payload.status.value
    )


@router.patch("/{card_id}/spending-limit", response_model=CardRead)
async def change_card_spending_limit(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    card_id: int,
    payload: CardSpendingLimitUpdate,
    user: User = Depends(current_active_user),
):
    return await update_spending_limit(
        session=session, card_id=card_id, user=user, payload=payload
    )
