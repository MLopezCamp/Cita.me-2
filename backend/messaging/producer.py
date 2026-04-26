"""
Productor RabbitMQ — publica eventos a colas de forma async.
cita.me: la creación de citas se desacopla de notificaciones y estadísticas.
"""
import json
import logging
import aio_pika
from config import RABBITMQ_URL, EXCHANGE_CITAS

logger = logging.getLogger(__name__)

_connection = None
_channel = None
_exchange = None


async def _get_channel():
    """Obtener o crear el canal con RabbitMQ."""
    global _connection, _channel, _exchange

    if _channel and not _channel.is_closed:
        return _channel

    _connection = await aio_pika.connect_robust(RABBITMQ_URL)
    _channel = await _connection.channel()

    _exchange = await _channel.declare_exchange(
        EXCHANGE_CITAS,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
    logger.info("[cita.me/RABBITMQ] Canal y exchange declarados")
    return _channel


async def publish_event(routing_key: str, event_data: dict):
    """Publicar un evento a RabbitMQ."""
    try:
        channel = await _get_channel()

        message = aio_pika.Message(
            body=json.dumps(event_data, default=str).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await _exchange.publish(message, routing_key=routing_key)

        logger.info(
            "[cita.me/RABBITMQ] Publicado: %s | %s",
            routing_key,
            json.dumps(event_data, default=str),
        )
    except Exception as e:
        logger.error("[cita.me/RABBITMQ] Error publicando %s: %s", routing_key, e)


async def close_producer():
    """Cerrar conexión del productor."""
    global _connection, _channel, _exchange
    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info("[cita.me/RABBITMQ] Conexión cerrada")
    _connection = _channel = _exchange = None