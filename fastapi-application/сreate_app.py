import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis

from core.config import settings
from core.messaging.connection import init_rabbitmq, stop_rabbitmq
from core.messaging.worker import start_worker
from core.models import bank_db_helper, userdata_db_helper
from actions.delete_expired_tokens import delete_expired_tokens
from middlewares import middlewares

log = logging.getLogger(__name__)


async def periodic_task():
    while True:
        await delete_expired_tokens()
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    redis = Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db.cache,
    )
    try:
        await redis.ping()
        FastAPICache.init(
            RedisBackend(redis),
            prefix=settings.cache.prefix,
            enable=True,
        )
        log.info("Redis cache initialised at %s:%s", settings.redis.host, settings.redis.port)
    except Exception as exc:
        log.warning("Redis unavailable (%s) — cache disabled, app starts without it", exc)
        FastAPICache.init(
            RedisBackend(redis),
            prefix=settings.cache.prefix,
            enable=False,
        )

    await init_rabbitmq()
    asyncio.create_task(periodic_task())
    asyncio.create_task(start_worker())

    yield
    # shutdown
    await redis.aclose()
    await userdata_db_helper.dispose()
    await bank_db_helper.dispose()
    await stop_rabbitmq()


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
    )

    middlewares(app)
    return app
