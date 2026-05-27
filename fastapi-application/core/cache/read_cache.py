"""
In-process TTL read cache with typed key builders and scoped invalidation.

Safe to cache:   accounts, cards, payments list, ledger list, transactions list,
                 beneficiaries, credits, deposits.
Never cached:    card reveal (raw PAN/CVV), documents, surveys, profile/onboarding.
"""

from __future__ import annotations

from copy import deepcopy
from time import monotonic
from typing import Any


_CACHE: dict[str, tuple[float, Any]] = {}

TTL_ACCOUNTS = 5
TTL_TRANSACTIONS = 10
TTL_PAYMENTS = 10
TTL_LEDGER = 10
TTL_CARDS = 15
TTL_BENEFICIARIES = 30
TTL_CREDITS = 30
TTL_DEPOSITS = 30


def get_cached(key: str) -> Any | None:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if expires_at <= monotonic():
        _CACHE.pop(key, None)
        return None
    return deepcopy(value)


def set_cached(key: str, value: Any, ttl_seconds: int) -> None:
    _CACHE[key] = (monotonic() + ttl_seconds, deepcopy(value))


def invalidate_cache_key(key: str) -> None:
    _CACHE.pop(key, None)


def invalidate_cache_prefix(prefix: str) -> None:
    for key in list(_CACHE):
        if key.startswith(prefix):
            _CACHE.pop(key, None)


def clear_read_cache() -> None:
    _CACHE.clear()


def cache_stats() -> dict[str, int]:
    now = monotonic()
    alive = sum(1 for exp, _ in _CACHE.values() if exp > now)
    return {"total_keys": len(_CACHE), "alive_keys": alive}


# ---------------------------------------------------------------------------
# Key builders
# ---------------------------------------------------------------------------

def account_list_cache_key(user_id: int) -> str:
    return f"accounts:{user_id}:list"


def account_detail_cache_key(user_id: int, account_id: int) -> str:
    return f"accounts:{user_id}:detail:{account_id}"


def card_list_cache_key(user_id: int) -> str:
    return f"cards:{user_id}:list"


def card_detail_cache_key(user_id: int, card_id: int) -> str:
    return f"cards:{user_id}:detail:{card_id}"


def transaction_list_cache_key(user_id: int) -> str:
    return f"transactions:{user_id}:list"


def payment_list_cache_key(user_id: int) -> str:
    return f"payments:{user_id}:list"


def ledger_list_cache_key(user_id: int, account_id: int | None = None) -> str:
    if account_id is not None:
        return f"ledger:{user_id}:account:{account_id}"
    return f"ledger:{user_id}:list"


def beneficiary_list_cache_key(user_id: int) -> str:
    return f"beneficiaries:{user_id}:list"


def credit_list_cache_key(user_id: int) -> str:
    return f"credits:{user_id}:list"


def deposit_list_cache_key(user_id: int) -> str:
    return f"deposits:{user_id}:list"


# ---------------------------------------------------------------------------
# Scoped invalidators
# ---------------------------------------------------------------------------

def invalidate_user_accounts_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"accounts:{user_id}:")


def invalidate_user_cards_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"cards:{user_id}:")


def invalidate_user_transactions_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"transactions:{user_id}:")


def invalidate_user_payments_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"payments:{user_id}:")


def invalidate_user_ledger_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"ledger:{user_id}:")


def invalidate_user_beneficiaries_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"beneficiaries:{user_id}:")


def invalidate_user_credits_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"credits:{user_id}:")


def invalidate_user_deposits_cache(user_id: int) -> None:
    invalidate_cache_prefix(f"deposits:{user_id}:")


def invalidate_all_for_user(user_id: int) -> None:
    """Drop every cached key that belongs to a user (e.g. on account close)."""
    for prefix in (
        f"accounts:{user_id}:",
        f"cards:{user_id}:",
        f"transactions:{user_id}:",
        f"payments:{user_id}:",
        f"ledger:{user_id}:",
        f"beneficiaries:{user_id}:",
        f"credits:{user_id}:",
        f"deposits:{user_id}:",
    ):
        invalidate_cache_prefix(prefix)
