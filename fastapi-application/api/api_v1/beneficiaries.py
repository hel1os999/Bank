from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users import current_active_user
from core.config import settings
from core.cache.key_builder import bank_key_builder
from core.models import User, bank_db_helper
from core.schemas.beneficiary import BeneficiaryCreate, BeneficiaryRead
from crud.beneficiaries import (
    create_beneficiary,
    delete_beneficiary,
    get_beneficiaries,
    get_beneficiary_by_id,
)

router = APIRouter(
    prefix=settings.api.v1.beneficiaries,
    tags=["Beneficiaries"],
)


@router.post("", response_model=BeneficiaryRead, status_code=status.HTTP_201_CREATED)
async def create_new_beneficiary(
    beneficiary: BeneficiaryCreate,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await create_beneficiary(session=session, beneficiary=beneficiary, user=user)


@router.get("", response_model=list[BeneficiaryRead])
@cache(
    expire=settings.cache.expire_beneficiaries,
    key_builder=bank_key_builder,
    namespace=settings.cache.namespace.beneficiaries_list,
)
async def list_beneficiaries(
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    user: User = Depends(current_active_user),
):
    return await get_beneficiaries(
        session=session, user=user, limit=limit, offset=offset
    )


@router.get("/{beneficiary_id}", response_model=BeneficiaryRead)
async def retrieve_beneficiary(
    beneficiary_id: int,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    return await get_beneficiary_by_id(
        session=session, beneficiary_id=beneficiary_id, user=user
    )


@router.delete("/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_beneficiary(
    beneficiary_id: int,
    session: Annotated[AsyncSession, Depends(bank_db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    await delete_beneficiary(session=session, beneficiary_id=beneficiary_id, user=user)
