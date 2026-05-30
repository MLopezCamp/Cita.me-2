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
from models import Horario, Doctor
from schemas import HorarioCreate, HorarioResponse
from messaging.producer import publish_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/horarios", tags=["Horarios"])

DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]


# =============================================================================
# Crear horario (admin, administrativo)
# =============================================================================
@router.post("/", response_model=HorarioResponse, status_code=201)
async def crear_horario(
    data: HorarioCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """Asignar un horario de atencion a un doctor. Requiere admin o administrativo."""

    # Verificar que el doctor existe
    doctor = await session.get(Doctor, data.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # Verificar que no se solape con horario existente
    stmt = select(Horario).where(
        and_(
            Horario.doctor_id == data.doctor_id,
            Horario.dia_semana == data.dia_semana,
            Horario.activo == True,
        )
    )
    result = await session.execute(stmt)
    existentes = result.scalars().all()

    for ex in existentes:
        if data.hora_inicio < ex.hora_fin and data.hora_fin > ex.hora_inicio:
            raise HTTPException(
                status_code=400,
                detail=f"El horario se solapa con uno existente "
                       f"({ex.hora_inicio} - {ex.hora_fin} los {DIAS[data.dia_semana]})"
            )

    horario = Horario(**data.model_dump())
    session.add(horario)
    await session.flush()

    await publish_event("horario.nuevo", {
        "horario_id": horario.id,
        "doctor_id": horario.doctor_id,
        "dia_semana": horario.dia_semana,
        "hora_inicio": str(horario.hora_inicio),
        "hora_fin": str(horario.hora_fin),
    })

    logger.info(
        "[HORARIO] %s #%s creo: doctor=%s, %s %s-%s",
        user["rol"], user["id"], data.doctor_id,
        DIAS[data.dia_semana], data.hora_inicio, data.hora_fin
    )
    return horario


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
    ).order_by(Horario.dia_semana, Horario.hora_inicio)

    result = await session.execute(stmt)
    return list(result.scalars().all())


# =============================================================================
# Actualizar horario (admin, administrativo)
# =============================================================================
@router.put("/{horario_id}", response_model=HorarioResponse)
async def actualizar_horario(
    horario_id: int,
    data: HorarioCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """
    Actualizar un horario existente (cambiar horas o dia).
    Requiere admin o administrativo.
    """
    horario = await session.get(Horario, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    # Verificar que no se solape con otro horario del mismo doctor
    stmt = select(Horario).where(
        and_(
            Horario.doctor_id == data.doctor_id,
            Horario.dia_semana == data.dia_semana,
            Horario.activo == True,
            Horario.id != horario_id,  # Excluir el horario actual
        )
    )
    result = await session.execute(stmt)
    existentes = result.scalars().all()

    for ex in existentes:
        if data.hora_inicio < ex.hora_fin and data.hora_fin > ex.hora_inicio:
            raise HTTPException(
                status_code=400,
                detail=f"El horario se solapa con uno existente "
                       f"({ex.hora_inicio} - {ex.hora_fin} los {DIAS[data.dia_semana]})"
            )

    horario.doctor_id = data.doctor_id
    horario.dia_semana = data.dia_semana
    horario.hora_inicio = data.hora_inicio
    horario.hora_fin = data.hora_fin
    await session.flush()

    logger.info(
        "[HORARIO] %s #%s actualizo horario #%s",
        user["rol"], user["id"], horario_id
    )
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

    await publish_event("horario.nuevo", {
        "horario_id": horario.id,
        "doctor_id": horario.doctor_id,
        "dia_semana": horario.dia_semana,
        "hora_inicio": str(horario.hora_inicio),
        "hora_fin": str(horario.hora_fin),
    })

    logger.info("[HORARIO] %s #%s activo horario #%s", user["rol"], user["id"], horario_id)
    return {"mensaje": "Horario activado exitosamente", "horario_id": horario_id}


# =============================================================================
# Desactivar horario (admin, administrativo)
# =============================================================================
@router.delete("/{horario_id}")
async def desactivar_horario(
    horario_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """Desactivar un horario (soft-delete). Requiere admin o administrativo."""
    horario = await session.get(Horario, horario_id)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    horario.activo = False
    await session.flush()

    logger.info(
        "[HORARIO] %s #%s desactivo horario #%s",
        user["rol"], user["id"], horario_id
    )
    return {"mensaje": "Horario desactivado exitosamente", "horario_id": horario_id}


# =============================================================================
# Listar todos los horarios del sistema (solo admin)
# =============================================================================
@router.get("/", response_model=list[HorarioResponse])
async def listar_todos_horarios(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Listar todos los horarios del sistema. Solo admin."""
    stmt = select(Horario).order_by(Horario.doctor_id, Horario.dia_semana, Horario.hora_inicio)
    result = await session.execute(stmt)
    return list(result.scalars().all())
