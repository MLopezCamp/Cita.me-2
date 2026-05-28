"""
cita.me — Portal del Paciente (protegido con JWT)

El paciente autenticado puede:
  - Ver sus citas (incluyendo canceladas y completadas)
  - Pedir nueva cita
  - Cancelar sus propias citas

"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import require_role, get_current_user
from models import Cita, Doctor
from schemas import CitaCreate, CitaResponse, CitaUpdateEstado
from services import cita_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portal", tags=["Portal Paciente"])


# =============================================================================
# Ver mis citas (solo paciente autenticado)
# =============================================================================
@router.get("/mis-citas")
async def mis_citas(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("paciente")),
):
    """Obtener todas las citas del paciente autenticado."""
    paciente_id = user["id"]  # Extraido del token JWT

    stmt = (
        select(Cita)
        .where(Cita.paciente_id == paciente_id)
        .order_by(Cita.fecha.desc(), Cita.hora.desc())
    )
    result = await session.execute(stmt)
    citas = result.scalars().all()

    # Enriquecer con datos del doctor
    respuesta = []
    for c in citas:
        doctor = await session.get(Doctor, c.doctor_id)
        respuesta.append({
            "id": c.id,
            "fecha": str(c.fecha),
            "hora": str(c.hora),
            "estado": c.estado,
            "motivo": c.motivo,
            "notas": c.notas,
            "doctor_id": c.doctor_id,
            "doctor_nombre": f"Dr. {doctor.nombre} {doctor.apellido}" if doctor else "Desconocido",
            "doctor_especialidad": doctor.especialidad if doctor else "",
            "creado_en": str(c.creado_en),
        })

    return respuesta


# =============================================================================
# Pedir nueva cita (solo paciente autenticado)
# =============================================================================
@router.post("/pedir-cita", response_model=CitaResponse, status_code=201)
async def pedir_cita(
    data: CitaCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("paciente")),
):
    """
    El paciente autenticado pide una cita.
    El paciente_id se sobreescribe con el ID del token para seguridad.
    """
    # Sobrescribir paciente_id con el del token (evita suplantacion)
    data.paciente_id = user["id"]

    try:
        cita = await cita_service.crear_cita(session, data)
        return cita
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


# =============================================================================
# Cancelar mi cita (solo paciente autenticado, solo sus citas)
# =============================================================================
@router.put("/cancelar/{cita_id}")
async def cancelar_mi_cita(
    cita_id: int,
    notas: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("paciente")),
):
    """
    El paciente cancela una de sus propias citas.
    Verifica que la cita pertenezca al paciente autenticado.
    """
    paciente_id = user["id"]  # Extraido del token JWT

    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Seguridad: verificar que la cita pertenece al paciente autenticado
    if cita.paciente_id != paciente_id:
        raise HTTPException(status_code=403, detail="Esta cita no le pertenece")

    if cita.estado == "cancelada":
        raise HTTPException(status_code=400, detail="La cita ya esta cancelada")

    if cita.estado == "completada":
        raise HTTPException(status_code=400, detail="No se puede cancelar una cita completada")

    data = CitaUpdateEstado(estado="cancelada", notas=notas)
    cita_actualizada = await cita_service.actualizar_estado(session, cita_id, data)

    logger.info(
        "[PORTAL] Paciente #%s cancelo cita #%s",
        paciente_id, cita_id
    )
    return {"mensaje": "Cita cancelada exitosamente", "cita_id": cita_id}


# =============================================================================
# Doctores disponibles (cualquier usuario autenticado)
# =============================================================================
@router.get("/doctores-disponibles")
async def doctores_para_portal(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """Lista simplificada de doctores activos para pedir citas."""
    stmt = select(Doctor).where(Doctor.activo == True).order_by(Doctor.apellido)
    result = await session.execute(stmt)
    doctores = result.scalars().all()

    return [
        {
            "id": d.id,
            "nombre": f"Dr. {d.nombre} {d.apellido}",
            "especialidad": d.especialidad,
        }
        for d in doctores
    ]
