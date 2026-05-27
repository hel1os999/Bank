from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import enum_value
from core.cache.cache_utils import invalidate_namespace
from core.config import settings
from core.crypto import generate_card_search_hash
from core.models import Beneficiary, User
from core.schemas.beneficiary import BeneficiaryCreate


async def create_beneficiary(
    session: AsyncSession, beneficiary: BeneficiaryCreate, user: User
):
    card_token = (
        generate_card_search_hash(beneficiary.card_number)
        if beneficiary.card_number
        else None
    )
    new_beneficiary = Beneficiary(
        user_id=user.id,
        name=beneficiary.name,
        iban=beneficiary.iban,
        card_token=card_token,
        currency=enum_value(beneficiary.currency),
        status="ACTIVE",
        created_at=datetime.now(),
    )
    session.add(new_beneficiary)
    await session.commit()
    await session.refresh(new_beneficiary)
    await invalidate_namespace(settings.cache.namespace.beneficiaries_list)
    return new_beneficiary


async def get_beneficiaries(
    session: AsyncSession, user: User, limit: int = 50, offset: int = 0
):
    stmt = (
        select(Beneficiary)
        .where(Beneficiary.user_id == user.id)
        .order_by(Beneficiary.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_beneficiary_model(
    session: AsyncSession, beneficiary_id: int, user: User
) -> Beneficiary:
    stmt = select(Beneficiary).where(
        Beneficiary.id == beneficiary_id, Beneficiary.user_id == user.id
    )
    result = await session.execute(stmt)
    beneficiary = result.scalars().first()
    if not beneficiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found"
        )
    return beneficiary


async def get_beneficiary_by_id(
    session: AsyncSession, beneficiary_id: int, user: User
):
    return await get_beneficiary_model(session, beneficiary_id, user)


async def delete_beneficiary(
    session: AsyncSession, beneficiary_id: int, user: User
) -> None:
    beneficiary = await get_beneficiary_model(session, beneficiary_id, user)
    await session.delete(beneficiary)
    await session.commit()
    await invalidate_namespace(settings.cache.namespace.beneficiaries_list)
