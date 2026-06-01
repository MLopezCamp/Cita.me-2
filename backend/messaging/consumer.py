"""
cita.me — Consumer RabbitMQ.
Procesa eventos de citas, partes medicos y horarios.
"""
import json
import asyncio
import logging
from datetime import date, timedelta

import aio_pika
from sqlalchemy import select, and_

from config import RABBITMQ_URL, EXCHANGE_CITAS, QUEUE_CITAS
from database import AsyncSessionLocal
from middleware.request_id import request_id_var
from models import Cita, Doctor, Paciente, ParteMedico
from messaging.email_service import (
    send_cita_creada,
    send_cita_estado_actualizado,
    send_cita_completada,
    send_nuevos_horarios,
)

logger = logging.getLogger("rabbitmq.worker")

EXTRA_ROUTING_KEYS = ["parte_medico.#", "horario.#"]


async def start_consumer():
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=5)

        exchange = await channel.declare_exchange(EXCHANGE_CITAS, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(QUEUE_CITAS, durable=True)
        await queue.bind(exchange, routing_key="cita.#")
        for rk in EXTRA_ROUTING_KEYS:
            await queue.bind(exchange, routing_key=rk)

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
            request_id_var.set(request_id)

            logger.info(
                "[WORKER] [%s] Evento: %s — payload: %s",
                request_id, routing_key, json.dumps(body, default=str),
            )

            if routing_key == "cita.creada":
                await _handle_cita_creada(body, request_id)
            elif routing_key == "cita.estado_actualizado":
                await _handle_cita_estado_actualizado(body, request_id)
            elif routing_key == "parte_medico.creado":
                await _handle_parte_medico_creado(body, request_id)
            elif routing_key in ("horario.nuevo", "horario.lote_nuevo"):
                await _handle_horario_lote_nuevo(body, request_id)
            else:
                await asyncio.sleep(0.1)

            logger.info("[WORKER] [%s] Tarea completada: %s", request_id, routing_key)

        except Exception as e:
            logger.error("[WORKER] Error procesando mensaje: %s", e)


async def _handle_cita_creada(body: dict, request_id: str):
    cita_id = body.get("cita_id")
    if not cita_id:
        return

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Cita, Paciente, Doctor)
            .join(Paciente, Cita.paciente_id == Paciente.id)
            .join(Doctor, Cita.doctor_id == Doctor.id)
            .where(Cita.id == cita_id)
        )
        row = (await session.execute(stmt)).first()
        if not row:
            logger.warning("[WORKER] [%s] Cita #%s no encontrada", request_id, cita_id)
            return
        cita, paciente, doctor = row

    await send_cita_creada(
        paciente_email=paciente.email,
        paciente_nombre=f"{paciente.nombre} {paciente.apellido}",
        fecha=str(cita.fecha),
        hora=str(cita.hora),
        especialidad=doctor.especialidad,
        doctor_nombre=f"Dr. {doctor.nombre} {doctor.apellido}",
        motivo=cita.motivo,
    )
    logger.info("[WORKER] [%s] Email de cita registrada enviado — cita #%s", request_id, cita_id)


async def _handle_cita_estado_actualizado(body: dict, request_id: str):
    cita_id = body.get("cita_id")
    nuevo_estado = body.get("nuevo_estado")
    if not cita_id or not nuevo_estado:
        return

    # Solo notificar estados relevantes para el paciente
    if nuevo_estado not in ("confirmada", "cancelada"):
        return

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Cita, Paciente, Doctor)
            .join(Paciente, Cita.paciente_id == Paciente.id)
            .join(Doctor, Cita.doctor_id == Doctor.id)
            .where(Cita.id == cita_id)
        )
        row = (await session.execute(stmt)).first()
        if not row:
            logger.warning("[WORKER] [%s] Cita #%s no encontrada", request_id, cita_id)
            return
        cita, paciente, doctor = row

    await send_cita_estado_actualizado(
        paciente_email=paciente.email,
        paciente_nombre=f"{paciente.nombre} {paciente.apellido}",
        fecha=str(cita.fecha),
        hora=str(cita.hora),
        especialidad=doctor.especialidad,
        doctor_nombre=f"Dr. {doctor.nombre} {doctor.apellido}",
        nuevo_estado=nuevo_estado,
    )
    logger.info(
        "[WORKER] [%s] Email de estado '%s' enviado — cita #%s",
        request_id, nuevo_estado, cita_id,
    )


async def _handle_parte_medico_creado(body: dict, request_id: str):
    cita_id = body.get("cita_id")
    if not cita_id:
        return

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Cita, Paciente, Doctor)
            .join(Paciente, Cita.paciente_id == Paciente.id)
            .join(Doctor, Cita.doctor_id == Doctor.id)
            .where(Cita.id == cita_id)
        )
        row = (await session.execute(stmt)).first()
        if not row:
            logger.warning("[WORKER] [%s] Cita #%s no encontrada para parte medico", request_id, cita_id)
            return

        cita, paciente, doctor = row

        parte_stmt = select(ParteMedico).where(ParteMedico.cita_id == cita_id)
        parte = (await session.execute(parte_stmt)).scalar_one_or_none()

    await send_cita_completada(
        paciente_email=paciente.email,
        paciente_nombre=f"{paciente.nombre} {paciente.apellido}",
        fecha=str(cita.fecha),
        hora=str(cita.hora),
        especialidad=doctor.especialidad,
        doctor_nombre=f"Dr. {doctor.nombre} {doctor.apellido}",
        notas=cita.notas,
        diagnostico=parte.diagnostico if parte else None,
        tratamiento=parte.tratamiento if parte else None,
        observaciones=parte.observaciones if parte else None,
    )
    logger.info("[WORKER] [%s] Email de cita completada enviado — cita #%s", request_id, cita_id)


async def _handle_horario_lote_nuevo(body: dict, request_id: str):
    """
    Notifica a pacientes con citas pendientes/confirmadas en la especialidad
    sobre nuevos horarios disponibles.
    Regla: solo se notifica al paciente sobre fechas que esten al menos 3 dias
    despues de su proxima cita (evita ruido cuando el slot es demasiado cercano).
    """
    doctor_id = body.get("doctor_id")
    fechas_raw = body.get("fechas", [])
    hora_inicio = body.get("hora_inicio")
    hora_fin = body.get("hora_fin")

    if not doctor_id or not fechas_raw:
        return

    # Parsear fechas del evento
    nuevas_fechas: list[date] = []
    for f in fechas_raw:
        try:
            nuevas_fechas.append(date.fromisoformat(str(f)))
        except Exception:
            pass

    if not nuevas_fechas:
        return

    hoy = date.today()

    async with AsyncSessionLocal() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            return

        # Pacientes con citas futuras pendientes/confirmadas en la misma especialidad
        stmt = (
            select(Cita, Paciente)
            .join(Doctor, Cita.doctor_id == Doctor.id)
            .join(Paciente, Cita.paciente_id == Paciente.id)
            .where(
                and_(
                    Doctor.especialidad == doctor.especialidad,
                    Cita.estado.in_(["pendiente", "confirmada"]),
                    Cita.fecha >= hoy,
                )
            )
            .order_by(Cita.fecha)
        )
        rows = (await session.execute(stmt)).all()

        # Por cada paciente, guardar su cita mas proxima
        paciente_proxima_cita: dict[int, tuple[date, Paciente]] = {}
        for cita, paciente in rows:
            if paciente.id not in paciente_proxima_cita:
                paciente_proxima_cita[paciente.id] = (cita.fecha, paciente)

        pacientes_notificados = 0
        for paciente_id, (cita_fecha, paciente) in paciente_proxima_cita.items():
            # Solo incluir fechas que sean >= cita_del_paciente + 3 dias
            fechas_aplicables = [
                f for f in nuevas_fechas
                if f >= cita_fecha + timedelta(days=3)
            ]
            if not fechas_aplicables:
                continue

            await send_nuevos_horarios(
                paciente_email=paciente.email,
                paciente_nombre=f"{paciente.nombre} {paciente.apellido}",
                especialidad=doctor.especialidad,
                doctor_nombre=f"Dr. {doctor.nombre} {doctor.apellido}",
                fechas=[str(f) for f in sorted(fechas_aplicables)],
                hora_inicio=str(hora_inicio),
                hora_fin=str(hora_fin),
            )
            pacientes_notificados += 1

    logger.info(
        "[WORKER] [%s] Notificaciones de horarios enviadas — doctor #%s, %d fechas, %d pacientes",
        request_id, doctor_id, len(nuevas_fechas), pacientes_notificados,
    )
