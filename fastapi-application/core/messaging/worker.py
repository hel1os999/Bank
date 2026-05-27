import asyncio

import logging

import log_settings

from core.crypto import decrypt_data
from core.models import bank_db_helper
from core.config import settings
from core.messaging.connection import get_channel
from core.messaging.consumer import consume_message
from crud.payments import process_payment
from crud.transactions import process_card_transfer

log = logging.getLogger("RMQ_LOGGER")


async def handle_payments(message):
    try:
        decrypted_data = decrypt_data(message)
        payment_id = decrypted_data["payment_id"]

        async with bank_db_helper.session_factory() as session:
            await process_payment(session=session, payment_id=payment_id)

    except Exception as e:
        log.error(f"Error in handle_payments", extra={"Error": e})


async def handle_transactions(message):
    try:
        decrypted_data = decrypt_data(message)
        transaction_id = decrypted_data["transaction_id"]

        async with bank_db_helper.session_factory() as session:
            await process_card_transfer(session=session, transaction_id=transaction_id)

    except Exception as e:
        log.error(f"Error in handle_transactions", extra={"Error": e})


async def start_worker():
    while True:
        try:
            log.info("Connecting to RabbitMQ...")
            async for channel in get_channel():
                await channel.set_qos(prefetch_count=10)
                log.info("Worker is successfully running. Waiting for messages...")

                await asyncio.gather(
                    consume_message(
                        channel, settings.rmq.payments_routing_key, handle_payments
                    ),
                    consume_message(
                        channel,
                        settings.rmq.transactions_routing_key,
                        handle_transactions,
                    ),
                )
        except Exception as e:
            log.error(f"Worker crashed. Retrying in 5s", extra={"Error": e})
            await asyncio.sleep(5)
