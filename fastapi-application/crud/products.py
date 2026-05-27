from datetime import datetime

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import decrypt_money, encrypt_money
from core.cache.cache_utils import invalidate_namespace
from core.config import settings
from core.models import Account, Credit, Deposit, User
from core.schemas.credit import CreditCreate
from core.schemas.deposit import DepositCreate
from crud.payments import _get_active_account


async def create_credit(
    session: AsyncSession, credit: CreditCreate, account_id: int, user: User
):
    account = await _get_active_account(session, account_id, user.id)
    now = datetime.now()
    new_credit = Credit(
        user_id=user.id,
        account_id=account.id,
        principal_amount=encrypt_money(credit.principal_amount),
        outstanding_amount=encrypt_money(credit.principal_amount),
        interest_rate=credit.interest_rate,
        status="ACTIVE",
        created_at=now,
        next_payment_date=now + relativedelta(months=1),
    )
    session.add(new_credit)
    await session.commit()
    await session.refresh(new_credit)
    await invalidate_namespace(settings.cache.namespace.credits_list)
    return serialize_credit(new_credit)


async def get_credits(
    session: AsyncSession, user: User, limit: int = 50, offset: int = 0
):
    result = await session.execute(
        select(Credit)
        .where(Credit.user_id == user.id)
        .order_by(Credit.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [serialize_credit(credit) for credit in result.scalars().all()]


async def create_deposit(
    session: AsyncSession, deposit: DepositCreate, account_id: int, user: User
):
    account = await _get_active_account(session, account_id, user.id)
    now = datetime.now()
    new_deposit = Deposit(
        user_id=user.id,
        account_id=account.id,
        principal_amount=encrypt_money(deposit.principal_amount),
        interest_rate=deposit.interest_rate,
        term_months=deposit.term_months,
        status="ACTIVE",
        opened_at=now,
        maturity_date=now + relativedelta(months=deposit.term_months),
    )
    session.add(new_deposit)
    await session.commit()
    await session.refresh(new_deposit)
    await invalidate_namespace(settings.cache.namespace.deposits_list)
    return serialize_deposit(new_deposit)


async def get_deposits(
    session: AsyncSession, user: User, limit: int = 50, offset: int = 0
):
    result = await session.execute(
        select(Deposit)
        .where(Deposit.user_id == user.id)
        .order_by(Deposit.opened_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [serialize_deposit(deposit) for deposit in result.scalars().all()]


async def get_credit_by_id(session: AsyncSession, credit_id: int, user: User):
    result = await session.execute(
        select(Credit).where(Credit.id == credit_id, Credit.user_id == user.id)
    )
    credit = result.scalars().first()
    if not credit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit not found")
    return serialize_credit(credit)


async def get_deposit_by_id(session: AsyncSession, deposit_id: int, user: User):
    result = await session.execute(
        select(Deposit).where(Deposit.id == deposit_id, Deposit.user_id == user.id)
    )
    deposit = result.scalars().first()
    if not deposit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")
    return serialize_deposit(deposit)


def serialize_credit(credit: Credit) -> dict:
    return {
        "id": credit.id,
        "user_id": credit.user_id,
        "account_id": credit.account_id,
        "principal_amount": decrypt_money(credit.principal_amount),
        "outstanding_amount": decrypt_money(credit.outstanding_amount),
        "interest_rate": credit.interest_rate,
        "status": credit.status,
        "created_at": credit.created_at,
        "next_payment_date": credit.next_payment_date,
    }


def serialize_deposit(deposit: Deposit) -> dict:
    return {
        "id": deposit.id,
        "user_id": deposit.user_id,
        "account_id": deposit.account_id,
        "principal_amount": decrypt_money(deposit.principal_amount),
        "interest_rate": deposit.interest_rate,
        "term_months": deposit.term_months,
        "status": deposit.status,
        "opened_at": deposit.opened_at,
        "maturity_date": deposit.maturity_date,
    }
