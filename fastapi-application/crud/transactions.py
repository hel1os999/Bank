from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.banking import decrypt_money, encrypt_money, normalize_money
from core.cache.cache_utils import invalidate_namespace
from core.config import settings
from core.crypto import encrypt_data, generate_card_search_hash
from core.models import Account, Card, Transaction, User
from core.schemas.transactions import TransactionCreate
from crud.ledger import create_ledger_entry


async def create_pending_card_transfer(
    session: AsyncSession, transaction: TransactionCreate, user: User
):
    if transaction.idempotency_key is not None:
        existing = await session.execute(
            select(Transaction).where(
                Transaction.user_id == user.id,
                Transaction.idempotency_key == transaction.idempotency_key,
            )
        )
        existing_tx = existing.scalars().first()
        if existing_tx:
            return serialize_transaction(existing_tx)

    sender_stmt = (
        select(Card, Account)
        .join(Account)
        .where(Card.id == transaction.sender_card_id, Account.user_id == user.id)
        .with_for_update()
    )
    sender_result = await session.execute(sender_stmt)
    sender_row = sender_result.first()
    if not sender_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sender card not found"
        )

    sender_card, sender_account = sender_row
    if (
        sender_card.is_blocked
        or sender_card.status != "ACTIVE"
        or sender_account.status != "ACTIVE"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sender card or account is not active",
        )

    receiver_token = generate_card_search_hash(transaction.receiver_card_number)
    receiver_stmt = (
        select(Card, Account).join(Account).where(Card.token == receiver_token)
    )
    receiver_result = await session.execute(receiver_stmt)
    receiver_row = receiver_result.first()
    if not receiver_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receiver card not found"
        )

    receiver_card, receiver_account = receiver_row
    amount = normalize_money(transaction.amount)
    new_transaction = Transaction(
        user_id=user.id,
        sender_account_id=sender_account.id,
        sender_card_id=sender_card.id,
        receiver_card_id=receiver_card.id,
        receiver_card_number=encrypt_data(transaction.receiver_card_number),
        amount=encrypt_money(amount),
        transaction_type=transaction.transaction_type,
        status="PENDING",
        idempotency_key=transaction.idempotency_key,
        reference=transaction.reference,
        timestamp=datetime.now(),
    )
    session.add(new_transaction)
    await session.commit()
    await session.refresh(new_transaction)
    await invalidate_namespace(settings.cache.namespace.transactions_list)
    return serialize_transaction(new_transaction, transaction.receiver_card_number)


async def process_card_transfer(session: AsyncSession, transaction_id: int) -> dict:
    result = await session.execute(
        select(Transaction).where(Transaction.id == transaction_id).with_for_update()
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    if transaction.status in ("COMPLETED", "FAILED", "PROCESSING"):
        return serialize_transaction(transaction)

    transaction.status = "PROCESSING"
    await session.commit()

    #receiver_account = None
    try:
        sender_result = await session.execute(
            select(Card, Account)
            .join(Account)
            .where(
                Card.id == transaction.sender_card_id,
                Account.id == transaction.sender_account_id,
                Account.user_id == transaction.user_id,
            )
            .with_for_update()
        )
        sender_row = sender_result.first()
        receiver_result = await session.execute(
            select(Card, Account)
            .join(Account)
            .where(Card.id == transaction.receiver_card_id)
            .with_for_update()
        )
        receiver_row = receiver_result.first()
        if not sender_row or not receiver_row:
            raise ValueError("Sender or receiver card not found")

        sender_card, sender_account = sender_row
        receiver_card, receiver_account = receiver_row
        if (
            sender_card.is_blocked
            or sender_card.status != "ACTIVE"
            or sender_account.status != "ACTIVE"
        ):
            raise ValueError("Sender card or account is not active")
        if receiver_card.is_blocked or receiver_card.status != "ACTIVE":
            raise ValueError("Receiver card is not active")

        amount = decrypt_money(transaction.amount)
        sender_balance = decrypt_money(sender_account.available_balance)
        if sender_balance < amount:
            raise ValueError("Insufficient funds")

        receiver_balance = decrypt_money(receiver_account.available_balance)
        new_sender_balance = normalize_money(sender_balance - amount)
        new_receiver_balance = normalize_money(receiver_balance + amount)
        sender_account.balance = encrypt_money(new_sender_balance)
        sender_account.available_balance = encrypt_money(new_sender_balance)
        receiver_account.balance = encrypt_money(new_receiver_balance)
        receiver_account.available_balance = encrypt_money(new_receiver_balance)
        transaction.status = "COMPLETED"
        transaction.failure_reason = None

        await create_ledger_entry(
            session,
            user_id=transaction.user_id,
            account_id=sender_account.id,
            transaction_id=transaction.id,
            entry_type="DEBIT",
            amount=amount,
            currency=sender_account.currency,
            balance_after=new_sender_balance,
            description=transaction.reference,
        )
        await create_ledger_entry(
            session,
            user_id=receiver_account.user_id,
            account_id=receiver_account.id,
            transaction_id=transaction.id,
            entry_type="CREDIT",
            amount=amount,
            currency=receiver_account.currency,
            balance_after=new_receiver_balance,
            description=transaction.reference,
        )
    except Exception as exc:
        transaction.status = "FAILED"
        transaction.failure_reason = str(exc)
        receiver_account = None

    await session.commit()
    await session.refresh(transaction)
    await invalidate_namespace(settings.cache.namespace.accounts_list)
    await invalidate_namespace(settings.cache.namespace.accounts_detail)
    await invalidate_namespace(settings.cache.namespace.transactions_list)
    await invalidate_namespace(settings.cache.namespace.ledger_list)
    return serialize_transaction(transaction)


async def get_transaction_by_id(
    session: AsyncSession, transaction_id: int, user: User
):
    result = await session.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == user.id
        )
    )
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    return serialize_transaction(transaction)


async def get_transactions(
    session: AsyncSession,
    user: User,
    limit: int = 50,
    offset: int = 0,
    card_id: int | None = None,
    account_id: int | None = None,
):
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    if card_id is not None:
        stmt = stmt.where(Transaction.sender_card_id == card_id)
    if account_id is not None:
        stmt = stmt.where(Transaction.sender_account_id == account_id)
    result = await session.execute(stmt)
    return [
        serialize_transaction(transaction) for transaction in result.scalars().all()
    ]


def serialize_transaction(
    transaction: Transaction, receiver_card_number: str | None = None
) -> dict:
    return {
        "id": transaction.id,
        "user_id": transaction.user_id,
        "sender_account_id": transaction.sender_account_id,
        "sender_card_id": transaction.sender_card_id,
        "receiver_card_id": transaction.receiver_card_id,
        "receiver_card_number": receiver_card_number or "****",
        "amount": decrypt_money(transaction.amount),
        "transaction_type": transaction.transaction_type,
        "status": transaction.status,
        "idempotency_key": transaction.idempotency_key,
        "reference": transaction.reference,
        "failure_reason": transaction.failure_reason,
        "timestamp": transaction.timestamp,
    }
