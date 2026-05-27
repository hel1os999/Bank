from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import log_settings

from core.config import settings

from aio_pika import Message, DeliveryMode

from core.serializer import MessageSerializer

if TYPE_CHECKING:
    from aio_pika.abc import AbstractRobustChannel

log = logging.getLogger("RMQ_LOGGER")


async def produce_message(
    message, channel: AbstractRobustChannel, routing_key: str | None = None
) -> None:
    routing_key = routing_key or settings.rmq.payments_routing_key
    queue = await channel.declare_queue(name=routing_key, durable=True)
    log.info("Declared queue", extra={"Routing Key": routing_key, "Queue": queue})

    rmq_message = Message(
        body=MessageSerializer.serialize(message),
        delivery_mode=DeliveryMode.PERSISTENT,
    )

    log.info("Publish message", extra={"Message": rmq_message.body.decode()})
    await channel.default_exchange.publish(
        message=rmq_message,
        routing_key=routing_key,
    )
    log.warning("Published message", extra={"Message": rmq_message.body.decode()})
