import logging

import aio_pika

import log_settings

from core.config import settings

log = logging.getLogger("RMQ_LOGGER")

_connection = None

async def init_rabbitmq():
    global _connection
    _connection = await aio_pika.connect_robust(settings.rmq.rmq_url)
    log.warning(f"Rabbitmq connection was created")
async def stop_rabbitmq():
    if _connection:
        await _connection.close()
        log.warning(f"Rabbitmq connection was closed")

async def get_channel():
    async with _connection.channel() as channel:
        log.warning(f"Rabbitmq channel was created")
        yield channel