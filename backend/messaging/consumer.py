"""
Consumidor RabbitMQ — procesa eventos de forma async.
cita.me: múltiples consumers procesan eventos en paralelo.
"""
import json
import asyncio
import logging
import aio_pika
from config import RABBITMQ_URL, EXCHANGE_CITAS, QUEUE_CITAS

logger = logging.getLogger(__name__)


async def start_consumer():
    """Iniciar el consumer como tarea en background."""
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()

        # Prefetch count = 5: procesa hasta 5 mensajes en paralelo
        await channel.set_qos(prefetch_count=5)

        exchange = await channel.declare_exchange(
            EXCHANGE_CITAS,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await channel.declare_queue(
            QUEUE_CITAS,
            durable=True,
        )

        await queue.bind(exchange, routing_key="cita.#")

        logger.info("[cita.me/CONSUMER] Escuchando en cola: %s", QUEUE_CITAS)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                asyncio.create_task(_process_message(message))

    except Exception as e:
        logger.error("[cita.me/CONSUMER] Error conectando: %s", e)
        await asyncio.sleep(5)
        await start_consumer()


async def _process_message(message: aio_pika.IncomingMessage):
    """Procesar un mensaje individual como coroutine."""
    async with message.process():
        try:
            body = json.loads(message.body.decode("utf-8"))
            routing_key = message.routing_key
            logger.info("[cita.me/CONSUMER] %s | %s", routing_key, body)

            if routing_key == "cita.creada":
                await _handle_cita_creada(body)
            elif routing_key == "cita.cancelada":
                await _handle_cita_cancelada(body)
            elif routing_key == "cita.estado_actualizado":
                await _handle_estado_actualizado(body)
            else:
                logger.warning("[cita.me/CONSUMER] Evento no manejado: %s", routing_key)

        except Exception as e:
            logger.error("[cita.me/CONSUMER] Error procesando mensaje: %s", e)


async def _handle_cita_creada(data: dict):
    await asyncio.sleep(0.5)
    logger.info(
        "[cita.me/CONSUMER] ✓ Notificación enviada — Cita #%s",
        data.get("cita_id"),
    )


async def _handle_cita_cancelada(data: dict):
    await asyncio.sleep(0.3)
    logger.info(
        "[cita.me/CONSUMER] ✓ Recursos liberados — Cita #%s cancelada",
        data.get("cita_id"),
    )


async def _handle_estado_actualizado(data: dict):
    await asyncio.sleep(0.2)
    logger.info(
        "[cita.me/CONSUMER] ✓ Estadísticas actualizadas — Cita #%s → %s",
        data.get("cita_id"),
        data.get("nuevo_estado"),
    )