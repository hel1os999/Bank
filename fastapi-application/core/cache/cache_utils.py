"""
Custom cache management utilities.

invalidate_namespace(namespace) scans Redis for all keys belonging
to a namespace and deletes them.  Call it after any write that
invalidates a group of cached responses.

Example:
    await invalidate_namespace(settings.cache.namespace.accounts_list)
    await invalidate_namespace(settings.cache.namespace.ledger_list)
"""

import logging

from fastapi_cache import FastAPICache

log = logging.getLogger(__name__)


async def invalidate_namespace(namespace: str) -> int:
    """
    Delete every Redis key whose name starts with ``{prefix}:{namespace}:``.

    Returns the number of deleted keys.
    Returns 0 silently if Redis is unreachable or the cache has not been
    initialised yet — write operations must never fail because of cache state.
    """
    try:
        backend = FastAPICache.get_backend()
        prefix = FastAPICache.get_prefix()
        redis = getattr(backend, "redis", None)
        if redis is None:
            return 0

        pattern = f"{prefix}:{namespace}:*"
        deleted = 0
        async for key in redis.scan_iter(match=pattern):
            await redis.delete(key)
            deleted += 1
        return deleted
    except Exception:
        log.warning("Cache invalidation skipped for namespace=%s (Redis unavailable)", namespace)
        return 0
