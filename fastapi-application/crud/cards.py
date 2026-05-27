import random
from datetime import datetime

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import decrypt_optional_money, encrypt_money, enum_value, mask_pan
from core.cache.cache_utils import invalidate_namespace
from core.config import settings
from core.crypto import decrypt_data, encrypt_data, generate_card_search_hash
from core.factories.card_factory import create_card_number
from core.models import Account, User
from core.models.card import Card
from core.schemas.card import CardCreate, CardSpendingLimitUpdate
from utils.get_last_four import get_last_four


async def create_card(
    card: CardCreate,
    account_id: int,
    user_session: AsyncSession,
    bank_session: AsyncSession,
    user: User,
):
    account_stmt = select(Account).where(
        Account.id == account_id, Account.user_id == user.id
    )
    result = await bank_session.execute(account_stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    if account.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account is not active"
        )

    card_number = create_card_number(enum_value(card.card_type), account_id)
    cvv = str(random.randint(100, 999))

    new_card = Card(
        account_id=account.id,
        CVV=encrypt_data(cvv),
        full_card_number=encrypt_data(card_number),
        last_four=get_last_four(card_number),
        validity_period=3,
        card_type=enum_value(card.card_type),
        token=generate_card_search_hash(card_number),
        created_at=datetime.now(),
        expiry_date=datetime.now() + relativedelta(years=3),
        is_blocked=False,
        spending_limit=encrypt_money(card.spending_limit),
        status="ACTIVE",
    )
    bank_session.add(new_card)
    await bank_session.commit()
    await bank_session.refresh(new_card)
    await invalidate_namespace(settings.cache.namespace.cards_list)
    return serialize_card(new_card)


async def get_cards(
    session: AsyncSession, user: User, limit: int = 50, offset: int = 0
):
    stmt = (
        select(Card)
        .join(Account)
        .where(Account.user_id == user.id)
        .order_by(Card.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return [serialize_card(card) for card in result.scalars().all()]


async def get_card_by_id(session: AsyncSession, card_id: int, user: User):
    return serialize_card(await get_owned_card_model(session, card_id, user))


async def get_reveal_card_by_id(
    session: AsyncSession,
    card_id: int,
    user: User,
):
    # Never cached — returns raw PAN/CVV
    card = await get_owned_card_model(session, card_id, user)
    if card.is_blocked or card.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Card is not active"
        )
    return {
        "full_pan": str(decrypt_data(card.full_card_number)),
        "cvv": str(decrypt_data(card.CVV)),
        "expiry_date": card.expiry_date,
    }


async def update_card_status(
    session: AsyncSession, card_id: int, user: User, status_value: str
):
    card = await get_owned_card_model(session, card_id, user)
    card.status = status_value
    card.is_blocked = status_value != "ACTIVE"
    await session.commit()
    await session.refresh(card)
    await invalidate_namespace(settings.cache.namespace.cards_list)
    await invalidate_namespace(settings.cache.namespace.cards_detail)
    return serialize_card(card)


async def get_owned_card_model(session: AsyncSession, card_id: int, user: User) -> Card:
    stmt = (
        select(Card).join(Account).where(Card.id == card_id, Account.user_id == user.id)
    )
    result = await session.execute(stmt)
    card = result.scalars().first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )
    return card


async def update_spending_limit(
    session: AsyncSession,
    card_id: int,
    user: User,
    payload: CardSpendingLimitUpdate,
):
    card = await get_owned_card_model(session, card_id, user)
    card.spending_limit = encrypt_money(payload.spending_limit)
    await session.commit()
    await session.refresh(card)
    await invalidate_namespace(settings.cache.namespace.cards_list)
    await invalidate_namespace(settings.cache.namespace.cards_detail)
    return serialize_card(card)


def serialize_card(card: Card) -> dict:
    return {
        "id": card.id,
        "account_id": card.account_id,
        "masked_pan": mask_pan(card.last_four),
        "last_four": card.last_four,
        "validity_period": card.validity_period,
        "card_type": card.card_type,
        "spending_limit": decrypt_optional_money(card.spending_limit) or 0,
        "token": card.token,
        "created_at": card.created_at,
        "expiry_date": card.expiry_date,
        "is_blocked": card.is_blocked,
        "status": card.status,
    }
