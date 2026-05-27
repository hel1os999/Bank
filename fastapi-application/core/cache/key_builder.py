"""
Cache key builder for fastapi-cache2.

Produces deterministic, user-scoped cache keys while excluding
infrastructure objects (DB sessions, RabbitMQ channels) that must
never be part of the cache key.

Usage:
    @cache(expire=60, key_builder=bank_key_builder, namespace=settings.cache.namespace.accounts_list)
    async def list_accounts(...):
        ...
"""

import hashlib
from typing import Any, Callable, Dict, Optional, Tuple

from aio_pika.abc import AbstractChannel
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession


_EXCLUDE_TYPES = (AsyncSession, AbstractChannel)


def bank_key_builder(
    func: Callable[..., Any],
    namespace: str,
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    cache_kw: Dict[str, Any] = {}
    for name, value in kwargs.items():
        if isinstance(value, _EXCLUDE_TYPES):
            continue
        # Represent the authenticated user by ID only (never serialize the full model)
        if hasattr(value, "id") and hasattr(value, "email"):
            cache_kw[name] = value.id
            continue
        cache_kw[name] = value

    raw = f"{func.__module__}:{func.__name__}:{args}:{cache_kw}"
    digest = hashlib.md5(raw.encode()).hexdigest()  # noqa: S324
    return f"{namespace}:{digest}"
