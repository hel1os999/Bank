"""
GET /health — dependency status check.

Returns 200 if all critical services are reachable, 503 otherwise.
Useful for Docker health checks, load balancers, and debugging.
"""

from fastapi import APIRouter, Response, status
from fastapi_cache import FastAPICache
from sqlalchemy import text

from core.models import bank_db_helper, userdata_db_helper

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Service health check",
    response_model=dict,
)
async def health_check(response: Response):
    checks: dict[str, str] = {}
    healthy = True

    # PostgreSQL — userdata
    try:
        async with userdata_db_helper.session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["userdata_db"] = "ok"
    except Exception as exc:
        checks["userdata_db"] = f"error: {exc}"
        healthy = False

    # PostgreSQL — bank
    try:
        async with bank_db_helper.session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["bank_db"] = "ok"
    except Exception as exc:
        checks["bank_db"] = f"error: {exc}"
        healthy = False

    # Redis / cache
    try:
        backend = FastAPICache.get_backend()
        redis = getattr(backend, "redis", None)
        if redis is None:
            checks["redis"] = "disabled"
        else:
            await redis.ping()
            checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        # Redis is optional — does not mark the service as unhealthy

    # RabbitMQ — check connection object exists and is not closed
    try:
        from core.messaging.connection import _connection
        if _connection is None:
            checks["rabbitmq"] = "not initialised"
            healthy = False
        elif _connection.is_closed:
            checks["rabbitmq"] = "error: connection closed"
            healthy = False
        else:
            checks["rabbitmq"] = "ok"
    except Exception as exc:
        checks["rabbitmq"] = f"error: {exc}"
        healthy = False

    response.status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "healthy" if healthy else "degraded", "checks": checks}
