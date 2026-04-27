"""
cita.me — Consumers especializados por servicio (comunicacion entre procesos).

Tres servicios desacoplados consumen de RabbitMQ:
1. servicio-notificaciones: Consume cita.creada, cita.confirmada, cita.cancelada
2. servicio-disponibilidad: Consume cita.creada, cita.cancelada
3. servicio-estadisticas: Consume cita.estado_actualizado, cita.creada

Cada servicio tiene su propia cola, su propio prefetch_count
y se ejecuta como tarea asyncio independiente.
"""
import json
import asyncio
import logging
import aio_pika
from config import RABBITMQ_URL, EXCHANGE_CITAS
from redis_client import cache_delete

logger = logging.getLogger(__name__)

SERVICIOS = {
    "notificaciones": {
        "queue": "citame.svc.notificaciones",
        "routing_keys": ["cita.creada", "cita.confirmada", "cita.cancelada"],
        "prefetch": 5,
    },
    "disponibilidad": {
        "queue": "citame.svc.disponibilidad",
        "routing_keys": ["cita.creada", "cita.cancelada"],
        "prefetch": 3,
    },
    "estadisticas": {
        "queue": "citame.svc.estadisticas",
        "routing_keys": ["cita.estado_actualizado", "cita.creada"],
        "prefetch": 10,
    },
}


async def start_all_consumers():
    """Iniciar los tres servicios como tareas independientes."""
    tasks = []
    for nombre in SERVICIOS:
        task = asyncio.create_task(_start_service(nombre))
        tasks.append(task)
        logger.info("[cita.me/CONSUMER] Servicio %s iniciado", nombre)
    await asyncio.gather(*tasks)


async def _start_service(service_name: str):
    """Iniciar un servicio consumer especifico con reconexion automatica."""
    config = SERVICIOS[service_name]
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=config["prefetch"])

            exchange = await channel.declare_exchange(
                EXCHANGE_CITAS, aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(config["queue"], durable=True)

            for rk in config["routing_keys"]:
                await queue.bind(exchange, routing_key=rk)

            logger.info(
                "[cita.me/%s] Escuchando cola=%s prefetch=%d routing=%s",
                service_name, config["queue"], config["prefetch"], config["routing_keys"],
            )

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    asyncio.create_task(_route_message(service_name, message))

        except Exception as e:
            logger.error("[cita.me/%s] Desconectado: %s. Reconectando en 5s...", service_name, e)
            await asyncio.sleep(5)


async def _route_message(service_name: str, message: aio_pika.IncomingMessage):
    """Enrutar mensaje al handler correcto segun servicio."""
    async with message.process():
        try:
            body = json.loads(message.body.decode("utf-8"))
            rk = message.routing_key

            if service_name == "notificaciones":
                await _handle_notificacion(rk, body)
            elif service_name == "disponibilidad":
                await _handle_disponibilidad(rk, body)
            elif service_name == "estadisticas":
                await _handle_estadisticas(rk, body)

        except Exception as e:
            logger.error("[cita.me/%s] Error procesando: %s", service_name, e)


# ──────────────────────────────────────────────────
# SERVICIO 1: NOTIFICACIONES AL PACIENTE
# Consume cita.creada, cita.confirmada, cita.cancelada
# Simula envio de email/SMS sin bloquear la reserva
# ──────────────────────────────────────────────────

async def _handle_notificacion(routing_key: str, data: dict):
    """Servicio de notificaciones al paciente."""
    await asyncio.sleep(0.3)  # Simula latencia de servicio externo

    if routing_key == "cita.creada":
        logger.info(
            "[NOTIFICACIONES] Email enviado a paciente #%s: "
            "Su cita #%s fue creada para el %s a las %s",
            data.get("paciente_id"), data.get("cita_id"),
            data.get("fecha"), data.get("hora"),
        )
    elif routing_key == "cita.confirmada":
        logger.info(
            "[NOTIFICACIONES] Email a paciente #%s: "
            "Cita #%s ha sido confirmada",
            data.get("paciente_id"), data.get("cita_id"),
        )
    elif routing_key == "cita.cancelada":
        logger.info(
            "[NOTIFICACIONES] Email a paciente #%s: "
            "Cita #%s ha sido cancelada",
            data.get("paciente_id"), data.get("cita_id"),
        )


# ──────────────────────────────────────────────────
# SERVICIO 2: DISPONIBILIDAD
# Consume cita.creada, cita.cancelada
# Actualiza slots sin bloquear la reserva original
# ──────────────────────────────────────────────────

async def _handle_disponibilidad(routing_key: str, data: dict):
    """Servicio de disponibilidad: actualiza cache de slots en background."""
    await asyncio.sleep(0.1)

    doctor_id = data.get("doctor_id")
    fecha = data.get("fecha")
    if not doctor_id or not fecha:
        return

    await cache_delete(f"citame:disponibles:doctor_{doctor_id}:*")

    if routing_key == "cita.creada":
        logger.info(
            "[DISPONIBILIDAD] Slot ocupado: doctor #%s, fecha %s",
            doctor_id, fecha,
        )
    elif routing_key == "cita.cancelada":
        logger.info(
            "[DISPONIBILIDAD] Slot liberado: doctor #%s, fecha %s",
            doctor_id, fecha,
        )


# ──────────────────────────────────────────────────
# SERVICIO 3: ESTADISTICAS
# Consume cita.estado_actualizado, cita.creada
# Registra metricas en memoria
# ──────────────────────────────────────────────────

_contadores = {
    "citas_creadas": 0,
    "citas_confirmadas": 0,
    "citas_canceladas": 0,
    "citas_completadas": 0,
}


async def _handle_estadisticas(routing_key: str, data: dict):
    """Servicio de estadisticas: registra metricas por evento."""
    await asyncio.sleep(0.05)

    if routing_key == "cita.creada":
        _contadores["citas_creadas"] += 1
        logger.info("[ESTADISTICAS] Total creadas: %d", _contadores["citas_creadas"])
    elif routing_key == "cita.estado_actualizado":
        nuevo = data.get("nuevo_estado", "")
        clave = f"citas_{nuevo}"
        if clave in _contadores:
            _contadores[clave] += 1
        logger.info("[ESTADISTICAS] Estado -> %s: %s", nuevo, dict(_contadores))