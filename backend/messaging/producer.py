"""
cita.me — Productor RabbitMQ.
Publica eventos incluyendo el request_id en el payload.
"""
import json
import logging
import aio_pika
from config import RABBITMQ_URL, EXCHANGE_CITAS

logger = logging.getLogger("rabbitmq.producer")

_connection = None
_channel = None
_exchange = None


async def _get_channel():
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
    return _channel


async def publish_event(routing_key: str, event_data: dict, request_id: str = "-"):
    """Publicar evento incluyendo request_id en el payload."""
    try:
        channel = await _get_channel()

        # El request_id viaja dentro del mensaje al worker
        payload = {
            "request_id": request_id,
            **event_data,
        }

        message = aio_pika.Message(
            body=json.dumps(payload, default=str).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await _exchange.publish(message, routing_key=routing_key)

        logger.info(
            "[RABBITMQ] [%s] Mensaje enviado: %s",
            request_id, routing_key,
            extra={"service": "rabbitmq", "request_id": request_id},
        )
    except Exception as e:
        logger.error(
            "[RABBITMQ] [%s] Error enviando %s: %s",
            request_id, routing_key, e,
            extra={"service": "rabbitmq", "request_id": request_id},
        )


async def close_producer():
    global _connection, _channel, _exchange
    if _connection and not _connection.is_closed:
        await _connection.close()
    _connection = _channel = _exchange = None