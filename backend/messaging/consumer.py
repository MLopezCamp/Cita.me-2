"""
cita.me — Consumer RabbitMQ.
Extrae el request_id del payload para trazabilidad completa.
"""
import json
import asyncio
import logging
import aio_pika
from config import RABBITMQ_URL, EXCHANGE_CITAS, QUEUE_CITAS

logger = logging.getLogger("rabbitmq.worker")


async def start_consumer():
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=5)

        exchange = await channel.declare_exchange(EXCHANGE_CITAS, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(QUEUE_CITAS, durable=True)
        await queue.bind(exchange, routing_key="cita.#")

        logger.info("[WORKER] Escuchando en cola: %s", QUEUE_CITAS)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                asyncio.create_task(_process_message(message))

    except Exception as e:
        logger.error("[WORKER] Error conectando: %s", e)
        await asyncio.sleep(5)
        await start_consumer()


async def _process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            body = json.loads(message.body.decode("utf-8"))
            routing_key = message.routing_key
            request_id = body.get("request_id", "-")

            logger.info("[WORKER] [%s] Evento procesado: %s — payload: %s", request_id, routing_key, json.dumps(body, default=str))

            await asyncio.sleep(0.3)

            logger.info("[WORKER] [%s] Tarea completada: %s", request_id, routing_key)

        except Exception as e:
            logger.error("[WORKER] Error procesando mensaje: %s", e)