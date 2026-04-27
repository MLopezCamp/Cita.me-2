"""
cita.me — Servicio de citas con locking distribuido, semaforo y concurrencia explicita.

Flujo de creacion:
1. Semaforo distribuido (Redis INCR): limita reservas simultaneas globales
2. Lock distribuido explicito (Redis SET NX EX): bloquea el slot especifico
3. Validaciones en base de datos
4. Creacion de cita
5. Publicacion de evento a RabbitMQ (fire-and-forget, no bloquea)
6. Invalidacion de cache en Redis
7. Liberacion de semaforo (lock se libera por TTL automaticamente)
"""
import logging
import asyncio
from datetime import date, time, datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models import Cita, Doctor, Horario, Paciente
from schemas import CitaCreate, CitaUpdateEstado
from redis_client import (
    DistributedLock, cache_get, cache_set, cache_delete,
    set_lock_raw, acquire_semaphore, release_semaphore,
)
from messaging.producer import publish_event

logger = logging.getLogger(__name__)

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Semaphore a nivel de proceso (independiente del semaforo distribuido en Redis)
_PROCESS_SEMAPHORE = asyncio.Semaphore(5)


def _lock_key(doctor_id: int, fecha: date, hora: time) -> str:
    return f"doctor_{doctor_id}:fecha_{fecha}:hora_{hora}"


def _cache_key_cita(cita_id: int) -> str:
    return f"citame:cita:{cita_id}"


def _cache_key_disponibles(doctor_id: int, fecha: date) -> str:
    return f"citame:disponibles:doctor_{doctor_id}:fecha_{fecha}"


async def crear_cita(session: AsyncSession, data: CitaCreate) -> Cita:
    """
    Crear cita con locking distribuido explicito (SET NX EX)
    y semaforo distribuido para limitar concurrencia global.
    """
    lock_key = _lock_key(data.doctor_id, data.fecha, data.hora)

    # Semaforo distribuido en Redis: limitar reservas simultaneas globales
    semaforo_ok = await acquire_semaphore("reservas_global", limit=20, timeout=60)
    if not semaforo_ok:
        raise RuntimeError("Sistema saturado. Demasiadas reservas simultaneas. Intente en segundos.")

    #Lock distribuido explicito con SET NX EX 
    lock_ok = await set_lock_raw(lock_key, ttl=15)
    if not lock_ok:
        await release_semaphore("reservas_global")
        raise RuntimeError("Horario siendo reservado por otra persona. Intente en segundos.")

    try:
        logger.info("[cita.me] Lock explícito adquirido: %s", lock_key)

        # Verificar doctor
        doctor = await session.get(Doctor, data.doctor_id)
        if not doctor or not doctor.activo:
            raise ValueError("El doctor no existe o no está activo")

        # Verificar paciente
        paciente = await session.get(Paciente, data.paciente_id)
        if not paciente:
            raise ValueError("El paciente no existe")

        # Verificar horario del doctor para ese dia
        dia_semana = data.fecha.weekday()
        stmt_horario = select(Horario).where(
            and_(
                Horario.doctor_id == data.doctor_id,
                Horario.dia_semana == dia_semana,
                Horario.activo == True,
                Horario.hora_inicio <= data.hora,
                Horario.hora_fin > data.hora,
            )
        )
        resultado = await session.execute(stmt_horario)
        horario = resultado.scalar_one_or_none()

        if not horario:
            raise ValueError(
                f"El doctor no atiende los {DIAS_SEMANA[dia_semana]} a las {data.hora}"
            )

        # Verificar que no haya cita existente en ese slot
        stmt_conflicto = select(Cita).where(
            and_(
                Cita.doctor_id == data.doctor_id,
                Cita.fecha == data.fecha,
                Cita.hora == data.hora,
                Cita.estado != "cancelada",
            )
        )
        resultado = await session.execute(stmt_conflicto)
        conflicto = resultado.scalar_one_or_none()

        if conflicto:
            raise ValueError(
                f"Ya existe una cita activa para ese horario (Cita #{conflicto.id})"
            )

        # Crear la cita
        nueva_cita = Cita(
            paciente_id=data.paciente_id,
            doctor_id=data.doctor_id,
            fecha=data.fecha,
            hora=data.hora,
            motivo=data.motivo,
            estado="pendiente",
        )
        session.add(nueva_cita)
        await session.flush()

        logger.info("[cita.me] Cita #%s creada (lock raw + semáforo)", nueva_cita.id)

        # Publicar evento a RabbitMQ (fire-and-forget, no bloquea)
        await publish_event("cita.creada", {
            "cita_id": nueva_cita.id,
            "paciente_id": data.paciente_id,
            "doctor_id": data.doctor_id,
            "fecha": str(data.fecha),
            "hora": str(data.hora),
            "motivo": data.motivo,
            "timestamp": str(datetime.utcnow()),
        })

        # Invalidar cache de disponibilidad
        await cache_delete(f"citame:disponibles:doctor_{data.doctor_id}:*")

        return nueva_cita

    finally:
        # Liberar semaforo (el lock se libera solo por TTL EX=15)
        await release_semaphore("reservas_global")
        logger.info("[cita.me] Semáforo liberado para: %s", lock_key)


async def crear_cita_con_limite(session: AsyncSession, data: CitaCreate) -> Cita:
    """
    Crear cita con asyncio.Semaphore() explicito a nivel de proceso.
    Controla concurrencia dentro de este contenedor (independiente del semaforo Redis).
    """
    async with _PROCESS_SEMAPHORE:
        logger.info(
            "[cita.me/SEMAFORO-PROCESS] Adquirido, slots libres: %d",
            5 - _PROCESS_SEMAPHORE._value,
        )
        return await crear_cita(session, data)


async def obtener_cita(session: AsyncSession, cita_id: int) -> dict | None:
    """Obtener detalle de cita con cache en Redis."""
    cache_key = _cache_key_cita(cita_id)

    cached = await cache_get(cache_key)
    if cached:
        logger.debug("[cita.me] Cache hit: #%s", cita_id)
        return cached

    stmt = (
        select(Cita, Paciente, Doctor)
        .join(Paciente, Cita.paciente_id == Paciente.id)
        .join(Doctor, Cita.doctor_id == Doctor.id)
        .where(Cita.id == cita_id)
    )
    resultado = await session.execute(stmt)
    row = resultado.first()

    if not row:
        return None

    cita, paciente, doctor = row
    data = {
        "id": cita.id,
        "paciente_id": cita.paciente_id,
        "doctor_id": cita.doctor_id,
        "fecha": str(cita.fecha),
        "hora": str(cita.hora),
        "estado": cita.estado,
        "motivo": cita.motivo,
        "notas": cita.notas,
        "creado_en": str(cita.creado_en),
        "paciente_nombre": paciente.nombre,
        "paciente_apellido": paciente.apellido,
        "doctor_nombre": doctor.nombre,
        "doctor_apellido": doctor.apellido,
        "doctor_especialidad": doctor.especialidad,
    }

    await cache_set(cache_key, data)
    return data


async def actualizar_estado(session: AsyncSession, cita_id: int, data: CitaUpdateEstado) -> Cita | None:
    """Actualizar estado de cita y publicar eventos a RabbitMQ."""
    cita = await session.get(Cita, cita_id)
    if not cita:
        return None

    estado_anterior = cita.estado
    cita.estado = data.estado
    if data.notas is not None:
        cita.notas = data.notas

    await session.flush()

    await publish_event("cita.estado_actualizado", {
        "cita_id": cita.id,
        "estado_anterior": estado_anterior,
        "nuevo_estado": data.estado,
        "timestamp": str(datetime.utcnow()),
    })

    if data.estado == "confirmada":
        await publish_event("cita.confirmada", {
            "cita_id": cita.id,
            "paciente_id": cita.paciente_id,
            "timestamp": str(datetime.utcnow()),
        })

    if data.estado == "cancelada":
        await publish_event("cita.cancelada", {
            "cita_id": cita.id,
            "doctor_id": cita.doctor_id,
            "fecha": str(cita.fecha),
            "hora": str(cita.hora),
            "timestamp": str(datetime.utcnow()),
        })
        await cache_delete(f"citame:disponibles:doctor_{cita.doctor_id}:*")

    await cache_delete(_cache_key_cita(cita_id))

    logger.info("[cita.me] Estado #%s: %s → %s", cita_id, estado_anterior, data.estado)
    return cita


async def obtener_disponibles(session: AsyncSession, doctor_id: int, fecha: date) -> list[dict]:
    """Horarios disponibles con cache en Redis."""
    cache_key = _cache_key_disponibles(doctor_id, fecha)

    cached = await cache_get(cache_key)
    if cached is not None:
        logger.debug("[cita.me] Disponibles cache: doctor=%s, fecha=%s", doctor_id, fecha)
        return cached

    dia_semana = fecha.weekday()

    stmt_horarios = select(Horario).where(
        and_(
            Horario.doctor_id == doctor_id,
            Horario.dia_semana == dia_semana,
            Horario.activo == True,
        )
    )
    resultado = await session.execute(stmt_horarios)
    horarios = resultado.scalars().all()

    if not horarios:
        return []

    slots = []
    for horario in horarios:
        inicio = _time_to_minutes(horario.hora_inicio)
        fin = _time_to_minutes(horario.hora_fin)
        t = inicio
        while t + 30 <= fin:
            hora = _minutes_to_time(t)
            slots.append(hora)
            t += 30

    stmt_citas = select(Cita.hora).where(
        and_(
            Cita.doctor_id == doctor_id,
            Cita.fecha == fecha,
            Cita.estado != "cancelada",
        )
    )
    resultado = await session.execute(stmt_citas)
    horas_ocupadas = {row[0] for row in resultado.all()}

    disponibles = [
        {"hora": str(h), "disponible": h not in horas_ocupadas}
        for h in slots
    ]

    await cache_set(cache_key, disponibles, ttl=120)
    return disponibles


async def obtener_disponibilidad_multiple(
    doctor_ids: list[int], fecha: date, session: AsyncSession
) -> dict:
    """
    Consultar disponibilidad de multiples doctores en paralelo con asyncio.gather().
    Demuestra concurrencia explicita: N consultas lanzadas al mismo tiempo.
    """
    async def check_one(doctor_id: int) -> tuple[int, list]:
        slots = await obtener_disponibles(session, doctor_id, fecha)
        return (doctor_id, slots)

    resultados = await asyncio.gather(*[check_one(did) for did in doctor_ids])

    return {
        "fecha": str(fecha),
        "resultados": [
            {
                "doctor_id": did,
                "slots": slots,
                "disponibles": sum(1 for s in slots if s["disponible"]),
            }
            for did, slots in resultados
        ],
    }


async def listar_citas(session: AsyncSession, skip: int = 0, limit: int = 50) -> list[Cita]:
    stmt = select(Cita).order_by(Cita.fecha.desc(), Cita.hora.desc()).offset(skip).limit(limit)
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())


async def listar_citas_paciente(session: AsyncSession, paciente_id: int) -> list[Cita]:
    stmt = select(Cita).where(Cita.paciente_id == paciente_id).order_by(Cita.fecha.desc())
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())


async def listar_citas_doctor(session: AsyncSession, doctor_id: int) -> list[Cita]:
    stmt = select(Cita).where(Cita.doctor_id == doctor_id).order_by(Cita.fecha.desc())
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())


def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _minutes_to_time(m: int) -> time:
    return time(hour=m // 60, minute=m % 60)