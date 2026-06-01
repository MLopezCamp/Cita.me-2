"""
cita.me — Endpoints de horarios de doctores (protegidos con JWT)

Permisos:
  - admin: CRUD completo
  - administrativo: crear, listar, actualizar (no eliminar)
  - doctor, paciente: solo listar horarios
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import get_current_user, require_role, require_any_role
from models import Horario, Doctor, Cita
from schemas import HorarioCreate, HorarioLoteCreate, HorarioResponse
from messaging.producer import publish_event
from middleware.request_id import get_request_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/horarios", tags=["Horarios"])


def _hay_solapamiento(hora_inicio, hora_fin, existentes) -> bool:
    return any(hora_inicio < ex.hora_fin and hora_fin > ex.hora_inicio for ex in existentes)


# =============================================================================
# Crear horario unico (admin, administrativo)
# =============================================================================
@router.post("/", response_model=HorarioResponse, status_code=201)
async def crear_horario(
    data: HorarioCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """Asignar un horario de atencion a un doctor. Requiere admin o administrativo."""
    doctor = await session.get(Doctor, data.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    stmt = select(Horario).where(
        and_(Horario.doctor_id == data.doctor_id, Horario.fecha == data.fecha, Horario.activo == True)
    )
    existentes = (await session.execute(stmt)).scalars().all()

    if _hay_solapamiento(data.hora_inicio, data.hora_fin, existentes):
        raise HTTPException(status_code=400, detail=f"El horario se solapa con uno existente el {data.fecha}")

    horario = Horario(**data.model_dump())
    session.add(horario)
    await session.flush()

    await publish_event("horario.lote_nuevo", {
        "doctor_id": horario.doctor_id,
        "fechas": [str(horario.fecha)],
        "hora_inicio": str(horario.hora_inicio),
        "hora_fin": str(horario.hora_fin),
    }, request_id=get_request_id())

    logger.info("[HORARIO] %s #%s creo: doctor=%s, %s %s-%s",
                user["rol"], user["id"], data.doctor_id, data.fecha, data.hora_inicio, data.hora_fin)
    return horario


# =============================================================================
# Crear multiples horarios en lote (admin, administrativo)
# =============================================================================
@router.post("/lote", response_model=list[HorarioResponse], status_code=201)
async def crear_horarios_lote(
    data: HorarioLoteCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """Crear horarios para multiples fechas a la vez. Requiere admin o administrativo."""
    doctor = await session.get(Doctor, data.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    creados = []
    solapadas = []

    for fecha in data.fechas:
        stmt = select(Horario).where(
            and_(Horario.doctor_id == data.doctor_id, Horario.fecha == fecha, Horario.activo == True)
        )
        existentes = (await session.execute(stmt)).scalars().all()

        if _hay_solapamiento(data.hora_inicio, data.hora_fin, existentes):
            solapadas.append(str(fecha))
            continue

        horario = Horario(
            doctor_id=data.doctor_id,
            fecha=fecha,
            hora_inicio=data.hora_inicio,
            hora_fin=data.hora_fin,
        )
        session.add(horario)
        creados.append(horario)

    if not creados:
        raise HTTPException(status_code=400, detail=f"Todas las fechas se solapan con horarios existentes: {solapadas}")

    await session.flush()

    await publish_event("horario.lote_nuevo", {
        "doctor_id": data.doctor_id,
        "fechas": [str(h.fecha) for h in creados],
        "hora_inicio": str(creados[0].hora_inicio),
        "hora_fin": str(creados[0].hora_fin),
    }, request_id=get_request_id())

    logger.info("[HORARIO] %s #%s creo lote: doctor=%s, %d fechas, %d solapadas",
                user["rol"], user["id"], data.doctor_id, len(creados), len(solapadas))
    return creados


# =============================================================================
# Listar horarios de un doctor (cualquier usuario autenticado)
# =============================================================================
@router.get("/doctor/{doctor_id}", response_model=list[HorarioResponse])
async def listar_horarios_doctor(
    doctor_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """Obtener todos los horarios activos de un doctor. Requiere autenticacion."""
    stmt = select(Horario).where(
        and_(Horario.doctor_id == doctor_id, Horario.activo == True)
    ).order_by(Horario.fecha, Horario.hora_inicio)

    result = await session.execute(stmt)
    return list(result.scalars().all())


# =============================================================================
# Actualizar horario (admin, administrativo)
# — Bloqueado si hay citas confirmadas en ese slot
# =============================================================================
@router.put("/{horario_id}", response_model=HorarioResponse)
async def actualizar_horario(
    horario_id: int,
    data: HorarioCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """
    Actualizar fecha u horas de un horario. Rechaza si hay citas confirmadas en el slot actual.
    Requiere admin o administrativo.
    """
    horario = await session.get(Horario, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    # Bloquear si existe alguna cita confirmada dentro de este slot actual
    stmt_citas = select(Cita).where(
        and_(
            Cita.doctor_id == horario.doctor_id,
            Cita.fecha == horario.fecha,
            Cita.hora >= horario.hora_inicio,
            Cita.hora < horario.hora_fin,
            Cita.estado == "confirmada",
        )
    )
    cita_bloqueante = (await session.execute(stmt_citas)).scalar_one_or_none()
    if cita_bloqueante:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede modificar: hay una cita confirmada (#{cita_bloqueante.id}) en este horario"
        )

    # Verificar solapamiento con otros horarios en la nueva fecha
    stmt = select(Horario).where(
        and_(
            Horario.doctor_id == data.doctor_id,
            Horario.fecha == data.fecha,
            Horario.activo == True,
            Horario.id != horario_id,
        )
    )
    existentes = (await session.execute(stmt)).scalars().all()

    if _hay_solapamiento(data.hora_inicio, data.hora_fin, existentes):
        raise HTTPException(
            status_code=400,
            detail=f"El horario se solapa con uno existente el {data.fecha}"
        )

    horario.doctor_id = data.doctor_id
    horario.fecha = data.fecha
    horario.hora_inicio = data.hora_inicio
    horario.hora_fin = data.hora_fin
    await session.flush()

    logger.info("[HORARIO] %s #%s actualizo horario #%s", user["rol"], user["id"], horario_id)
    return horario


# =============================================================================
# Activar horario inactivo (admin, administrativo)
# =============================================================================
@router.put("/{horario_id}/activar")
async def activar_horario(
    horario_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """Reactivar un horario previamente desactivado. Notifica a pacientes con citas pendientes en la especialidad."""
    horario = await session.get(Horario, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    if horario.activo:
        raise HTTPException(status_code=400, detail="El horario ya esta activo")

    horario.activo = True
    await session.flush()

    await publish_event("horario.lote_nuevo", {
        "doctor_id": horario.doctor_id,
        "fechas": [str(horario.fecha)],
        "hora_inicio": str(horario.hora_inicio),
        "hora_fin": str(horario.hora_fin),
    }, request_id=get_request_id())

    logger.info("[HORARIO] %s #%s activo horario #%s", user["rol"], user["id"], horario_id)
    return {"mensaje": "Horario activado exitosamente", "horario_id": horario_id}


# =============================================================================
# Eliminar horario (admin, administrativo)
# =============================================================================
@router.delete("/{horario_id}")
async def eliminar_horario(
    horario_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """Eliminar un horario de la base de datos. Requiere admin o administrativo."""
    horario = await session.get(Horario, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    await session.delete(horario)
    await session.flush()

    logger.info("[HORARIO] %s #%s elimino horario #%s", user["rol"], user["id"], horario_id)
    return {"mensaje": "Horario eliminado exitosamente", "horario_id": horario_id}


# =============================================================================
# Listar todos los horarios del sistema (solo admin)
# =============================================================================
@router.get("/", response_model=list[HorarioResponse])
async def listar_todos_horarios(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Listar todos los horarios del sistema. Solo admin."""
    stmt = select(Horario).order_by(Horario.doctor_id, Horario.fecha, Horario.hora_inicio)
    result = await session.execute(stmt)
    return list(result.scalars().all())
