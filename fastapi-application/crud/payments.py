from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import decrypt_money, encrypt_money, enum_value, normalize_money
from core.cache.cache_utils import invalidate_namespace
from core.config import settings
from core.models import Account, Beneficiary, Payment, User
from core.schemas.payment import PaymentCreate
from crud.ledger import create_ledger_entry


async def create_payment(session: AsyncSession, payment: PaymentCreate, user: User):
    existing = await session.execute(
        select(Payment).where(
            Payment.user_id == user.id,
            Payment.idempotency_key == payment.idempotency_key,
        )
    )
    existing_payment = existing.scalars().first()
    if existing_payment:
        return serialize_payment(existing_payment)

    account = await _get_active_account(session, payment.account_id, user.id)
    beneficiary = None
    if payment.beneficiary_id is not None:
        beneficiary_result = await session.execute(
            select(Beneficiary).where(
                Beneficiary.id == payment.beneficiary_id,
                Beneficiary.user_id == user.id,
            )
        )
        beneficiary = beneficiary_result.scalars().first()
        if not beneficiary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found"
            )

    now = datetime.now()
    new_payment = Payment(
        user_id=user.id,
        account_id=account.id,
        beneficiary_id=beneficiary.id if beneficiary else None,
        amount=encrypt_money(payment.amount),
        currency=enum_value(payment.currency),
        status="PENDING",
        payment_type=payment.payment_type,
        counterparty_name=payment.counterparty_name
        or (beneficiary.name if beneficiary else None),
        counterparty_iban=payment.counterparty_iban
        or (beneficiary.iban if beneficiary else None),
        reference=payment.reference,
        idempotency_key=payment.idempotency_key,
        created_at=now,
        updated_at=now,
    )
    session.add(new_payment)
    await session.commit()
    await session.refresh(new_payment)
    await invalidate_namespace(settings.cache.namespace.payments_list)
    return serialize_payment(new_payment)


async def process_payment(session: AsyncSession, payment_id: int) -> dict:
    result = await session.execute(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    )
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    if payment.status in ("COMPLETED", "FAILED", "PROCESSING"):
        return serialize_payment(payment)

    payment.status = "PROCESSING"
    payment.updated_at = datetime.now()
    await session.commit()

    try:
        account = await _get_active_account(
            session, payment.account_id, payment.user_id, lock=True
        )
        amount = decrypt_money(payment.amount)
        available_balance = decrypt_money(account.available_balance)
        if available_balance < amount:
            raise ValueError("Insufficient funds")

        new_balance = normalize_money(available_balance - amount)
        account.balance = encrypt_money(new_balance)
        account.available_balance = encrypt_money(new_balance)
        payment.status = "COMPLETED"
        payment.updated_at = datetime.now()
        payment.completed_at = payment.updated_at
        payment.failure_reason = None
        await create_ledger_entry(
            session,
            user_id=payment.user_id,
            account_id=account.id,
            payment_id=payment.id,
            entry_type="DEBIT",
            amount=amount,
            currency=payment.currency,
            balance_after=new_balance,
            description=payment.reference,
        )
    except Exception as exc:
        payment.status = "FAILED"
        payment.failure_reason = str(exc)
        payment.updated_at = datetime.now()

    await session.commit()
    await session.refresh(payment)
    await invalidate_namespace(settings.cache.namespace.accounts_list)
    await invalidate_namespace(settings.cache.namespace.accounts_detail)
    await invalidate_namespace(settings.cache.namespace.payments_list)
    await invalidate_namespace(settings.cache.namespace.ledger_list)
    return serialize_payment(payment)


async def get_payments(
    session: AsyncSession, user: User, limit: int = 50, offset: int = 0
):
    stmt = (
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return [serialize_payment(payment) for payment in result.scalars().all()]


async def get_payment_by_id(session: AsyncSession, payment_id: int, user: User):
    stmt = select(Payment).where(Payment.id == payment_id, Payment.user_id == user.id)
    result = await session.execute(stmt)
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return serialize_payment(payment)


async def _get_active_account(
    session: AsyncSession, account_id: int, user_id: int, lock: bool = False
) -> Account:
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
    if lock:
        stmt = stmt.with_for_update()
    result = await session.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    if account.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account is not active"
        )
    return account


def serialize_payment(payment: Payment) -> dict:
    return {
        "id": payment.id,
        "user_id": payment.user_id,
        "account_id": payment.account_id,
        "beneficiary_id": payment.beneficiary_id,
        "amount": decrypt_money(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "payment_type": payment.payment_type,
        "counterparty_name": payment.counterparty_name,
        "counterparty_iban": payment.counterparty_iban,
        "reference": payment.reference,
        "idempotency_key": payment.idempotency_key,
        "failure_reason": payment.failure_reason,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
        "completed_at": payment.completed_at,
    }
