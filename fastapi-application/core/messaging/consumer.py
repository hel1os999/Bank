from __future__ import annotations

import asyncio
import logging

import log_settings

log = logging.getLogger("RMQ_LOGGER")

async def consume_message(channel, queue_name, callback):
    queue = await channel.declare_queue(queue_name, durable=True)

    log.info("Declared queue", extra={"queue": queue})

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            asyncio.create_task(process_message(message, callback))


async def process_message(message, callback):
    async with message.process():
        log.info("Starting message process", extra={"Message": message.body.decode()})
        data = message.body.decode()
        await callback(data)
