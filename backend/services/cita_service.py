"""
cita.me — Servicio de citas con locking distribuido.
"""
import logging
from datetime import date, time, datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models import Cita, Doctor, Horario, Paciente
from schemas import CitaCreate, CitaUpdateEstado
from redis_client import DistributedLock, cache_get, cache_set, cache_delete
from messaging.producer import publish_event

logger = logging.getLogger("api.citas")

def _lock_key(doctor_id: int, fecha: date, hora: time) -> str:
    return f"cita:doctor_{doctor_id}:fecha_{fecha}:hora_{hora}"


def _cache_key_cita(cita_id: int) -> str:
    return f"citame:cita:{cita_id}"


def _cache_key_disponibles(doctor_id: int, fecha: date) -> str:
    return f"citame:disponibles:doctor_{doctor_id}:fecha_{fecha}"


async def crear_cita(session: AsyncSession, data: CitaCreate, request_id: str = "-") -> Cita:

    lock = DistributedLock(
        _lock_key(data.doctor_id, data.fecha, data.hora),
        request_id=request_id,
    )

    logger.info("[API] [%s] Creando cita: doctor=%s, fecha=%s, hora=%s", request_id, data.doctor_id, data.fecha, data.hora)

    acquired = await lock.acquire()
    if not acquired:
        logger.warning("[API] [%s] Lock NO adquirido — alta demanda", request_id)
        raise RuntimeError("No se pudo reservar el horario. Intente en unos segundos.")

    try:
        doctor = await session.get(Doctor, data.doctor_id)
        if not doctor or not doctor.activo:
            raise ValueError("El doctor no existe o no está activo")

        paciente = await session.get(Paciente, data.paciente_id)
        if not paciente:
            raise ValueError("El paciente no existe")

        stmt_horario = select(Horario).where(
            and_(
                Horario.doctor_id == data.doctor_id,
                Horario.fecha == data.fecha,
                Horario.activo == True,
                Horario.hora_inicio <= data.hora,
                Horario.hora_fin > data.hora,
            )
        )
        resultado = await session.execute(stmt_horario)
        horario = resultado.scalar_one_or_none()

        if not horario:
            raise ValueError(f"El doctor no tiene horario habilitado el {data.fecha} a las {data.hora}")

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
            raise ValueError(f"Ya existe cita activa para ese horario (Cita #{conflicto.id})")

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

        logger.info("[API] [%s] Cita #%s creada en BD", request_id, nueva_cita.id)

        await publish_event("cita.creada", {
            "cita_id": nueva_cita.id,
            "paciente_id": data.paciente_id,
            "doctor_id": data.doctor_id,
            "fecha": str(data.fecha),
            "hora": str(data.hora),
            "motivo": data.motivo,
            "timestamp": str(datetime.utcnow()),
        }, request_id=request_id)

        await cache_delete(f"citame:disponibles:doctor_{data.doctor_id}:*", request_id=request_id)

        return nueva_cita

    finally:
        await lock.release()


async def obtener_cita(session: AsyncSession, cita_id: int, request_id: str = "-") -> dict | None:
    cache_key = _cache_key_cita(cita_id)
    cached = await cache_get(cache_key, request_id)
    if cached:
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

    await cache_set(cache_key, data, request_id=request_id)
    return data


async def actualizar_estado(session: AsyncSession, cita_id: int, data: CitaUpdateEstado, request_id: str = "-") -> Cita | None:
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
    }, request_id=request_id)

    if data.estado == "cancelada":
        await publish_event("cita.cancelada", {
            "cita_id": cita.id,
            "doctor_id": cita.doctor_id,
            "fecha": str(cita.fecha),
            "hora": str(cita.hora),
        }, request_id=request_id)
        await cache_delete(f"citame:disponibles:doctor_{cita.doctor_id}:*", request_id=request_id)

    await cache_delete(_cache_key_cita(cita_id), request_id=request_id)

    logger.info("[API] [%s] Estado #%s: %s -> %s", request_id, cita_id, estado_anterior, data.estado)
    return cita


async def obtener_disponibles(session: AsyncSession, doctor_id: int, fecha: date, request_id: str = "-") -> list[dict]:
    cache_key = _cache_key_disponibles(doctor_id, fecha)
    cached = await cache_get(cache_key, request_id)
    if cached is not None:
        return cached

    stmt_horarios = select(Horario).where(
        and_(
            Horario.doctor_id == doctor_id,
            Horario.fecha == fecha,
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
            slots.append(_minutes_to_time(t))
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

    await cache_set(cache_key, disponibles, ttl=120, request_id=request_id)
    return disponibles


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