from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import decrypt_money, encrypt_money, enum_value
from core.cache.cache_utils import invalidate_namespace
from core.config import settings
from core.crypto import decrypt_data, encrypt_data
from core.factories.IBAN_factory import create_iban
from core.models import UserDocument, User, UserSurvey, Account
from core.schemas.account import AccountCreate


async def create_account(
    account: AccountCreate,
    user_session: AsyncSession,
    bank_session: AsyncSession,
    user: User,
):
    stmt = select(UserSurvey).join(UserDocument).where(UserDocument.user_id == user.id)

    result = await user_session.execute(stmt)
    survey = result.scalars().first()

    if not survey:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete the customer survey before opening an account",
        )

    encrypted_balance = encrypt_money(account.balance)

    new_account = Account(
        user_id=user.id,
        user_survey_id=survey.id,
        balance=encrypted_balance,
        available_balance=encrypted_balance,
        limits=encrypt_money(account.limits),
        account_type=enum_value(account.account_type),
        currency=enum_value(account.currency),
        IBAN=encrypt_data(create_iban(str(user.id))),
        created_at=datetime.now(),
        status="ACTIVE",
    )

    bank_session.add(new_account)
    await bank_session.commit()
    await bank_session.refresh(new_account)
    await invalidate_namespace(settings.cache.namespace.accounts_list)
    return serialize_account(new_account)


async def get_accounts(
    session: AsyncSession, user: User, limit: int = 50, offset: int = 0
):
    stmt = (
        select(Account)
        .where(Account.user_id == user.id)
        .order_by(Account.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return [serialize_account(account) for account in result.scalars().all()]


async def get_account_by_id(session: AsyncSession, account_id: int, user: User):
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user.id)
    result = await session.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return serialize_account(account)


async def get_owned_account_model(
    session: AsyncSession, account_id: int, user: User
) -> Account:
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user.id)
    result = await session.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return account


async def update_account_status(
    session: AsyncSession, account_id: int, user: User, status_value: str
):
    account = await get_owned_account_model(session, account_id, user)
    account.status = status_value
    await session.commit()
    await session.refresh(account)
    await invalidate_namespace(settings.cache.namespace.accounts_list)
    await invalidate_namespace(settings.cache.namespace.accounts_detail)
    return serialize_account(account)


def serialize_account(account: Account) -> dict:
    return {
        "id": account.id,
        "user_id": account.user_id,
        "created_at": account.created_at,
        "user_survey_id": account.user_survey_id,
        "balance": decrypt_money(account.balance),
        "available_balance": decrypt_money(account.available_balance),
        "account_type": account.account_type,
        "currency": account.currency,
        "limits": decrypt_money(account.limits),
        "IBAN": decrypt_data(account.IBAN),
        "status": account.status,
    }
