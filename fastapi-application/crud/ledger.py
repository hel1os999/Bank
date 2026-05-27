from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import decrypt_money, encrypt_money, enum_value
from core.models import LedgerEntry, User


async def create_ledger_entry(
    session: AsyncSession,
    *,
    user_id: int,
    account_id: int,
    entry_type: str,
    amount,
    currency,
    balance_after,
    payment_id: int | None = None,
    transaction_id: int | None = None,
    description: str | None = None,
) -> LedgerEntry:
    entry = LedgerEntry(
        user_id=user_id,
        account_id=account_id,
        payment_id=payment_id,
        transaction_id=transaction_id,
        entry_type=entry_type,
        amount=encrypt_money(amount),
        currency=enum_value(currency),
        balance_after=encrypt_money(balance_after),
        description=description,
        created_at=datetime.now(),
    )
    session.add(entry)
    return entry


async def get_ledger(
    session: AsyncSession,
    user: User,
    account_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt = (
        select(LedgerEntry)
        .where(LedgerEntry.user_id == user.id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if account_id is not None:
        stmt = stmt.where(LedgerEntry.account_id == account_id)

    result = await session.execute(stmt)
    return [serialize_ledger_entry(entry) for entry in result.scalars().all()]


def serialize_ledger_entry(entry: LedgerEntry) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "account_id": entry.account_id,
        "payment_id": entry.payment_id,
        "transaction_id": entry.transaction_id,
        "entry_type": entry.entry_type,
        "amount": decrypt_money(entry.amount),
        "currency": entry.currency,
        "balance_after": decrypt_money(entry.balance_after),
        "description": entry.description,
        "created_at": entry.created_at,
    }
