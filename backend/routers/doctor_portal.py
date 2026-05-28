"""
cita.me — Portal del Doctor (protegido con JWT)

El doctor autenticado puede:
  - Ver sus citas asignadas (filtrar por estado opcional)
  - Confirmar citas pendientes
  - Completar citas con notas / parte medico
  - Cancelar sus citas

"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import require_role
from models import Cita, Paciente
from schemas import CitaUpdateEstado
from services import cita_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doctor-portal", tags=["Portal Doctor"])


# =============================================================================
# Ver mis citas (solo doctor autenticado)
# =============================================================================
@router.get("/mis-citas")
async def mis_citas(
    estado: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """
    Listar las citas asignadas al doctor autenticado.
    Opcionalmente filtrar por estado: pendiente, confirmada, cancelada, completada.
    """
    doctor_id = user["id"]  # Extraido del token JWT

    stmt = select(Cita).where(Cita.doctor_id == doctor_id)

    if estado:
        stmt = stmt.where(Cita.estado == estado)

    stmt = stmt.order_by(Cita.fecha.desc(), Cita.hora.desc())
    result = await session.execute(stmt)
    citas = result.scalars().all()

    # Enriquecer con datos del paciente
    respuesta = []
    for c in citas:
        paciente = await session.get(Paciente, c.paciente_id)
        respuesta.append({
            "id": c.id,
            "fecha": str(c.fecha),
            "hora": str(c.hora),
            "estado": c.estado,
            "motivo": c.motivo,
            "notas": c.notas,
            "paciente_id": c.paciente_id,
            "paciente_nombre": f"{paciente.nombre} {paciente.apellido}" if paciente else "Desconocido",
            "paciente_documento": paciente.documento if paciente else "",
            "creado_en": str(c.creado_en),
        })

    return respuesta


# =============================================================================
# Ver detalle de una cita (solo doctor autenticado, solo sus citas)
# =============================================================================
@router.get("/cita/{cita_id}")
async def detalle_cita(
    cita_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """Obtener el detalle completo de una cita del doctor autenticado."""
    doctor_id = user["id"]  # Extraido del token JWT

    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Esta cita no es suya")

    paciente = await session.get(Paciente, cita.paciente_id)

    return {
        "id": cita.id,
        "fecha": str(cita.fecha),
        "hora": str(cita.hora),
        "estado": cita.estado,
        "motivo": cita.motivo,
        "notas": cita.notas,
        "paciente_id": cita.paciente_id,
        "paciente_nombre": f"{paciente.nombre} {paciente.apellido}" if paciente else "Desconocido",
        "paciente_documento": paciente.documento if paciente else "",
        "paciente_telefono": paciente.telefono if paciente else "",
        "creado_en": str(cita.creado_en),
    }


# =============================================================================
# Confirmar cita pendiente (solo doctor autenticado, solo sus citas)
# =============================================================================
@router.put("/confirmar/{cita_id}")
async def confirmar_cita(
    cita_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """Confirmar una cita pendiente. Solo el doctor asignado puede confirmarla."""
    doctor_id = user["id"]  # Extraido del token JWT

    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Esta cita no es suya")

    if cita.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar citas pendientes")

    data = CitaUpdateEstado(estado="confirmada")
    await cita_service.actualizar_estado(session, cita_id, data)

    logger.info("[DOCTOR-PORTAL] Dr.#%s confirmo cita #%s", doctor_id, cita_id)
    return {"mensaje": "Cita confirmada exitosamente", "cita_id": cita_id}


# =============================================================================
# Completar cita con notas (solo doctor autenticado, solo sus citas)
# =============================================================================
@router.put("/completar/{cita_id}")
async def completar_cita(
    cita_id: int,
    notas: str,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """
    Marcar una cita como completada y agregar notas medicas.
    Solo el doctor asignado puede completarla.
    """
    doctor_id = user["id"]  # Extraido del token JWT

    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Esta cita no es suya")

    if cita.estado == "cancelada":
        raise HTTPException(status_code=400, detail="No se puede completar una cita cancelada")

    if cita.estado == "completada":
        raise HTTPException(status_code=400, detail="La cita ya fue completada")

    data = CitaUpdateEstado(estado="completada", notas=notas)
    await cita_service.actualizar_estado(session, cita_id, data)

    logger.info("[DOCTOR-PORTAL] Dr.#%s completo cita #%s", doctor_id, cita_id)
    return {
        "mensaje": "Cita completada exitosamente. Puede registrar el parte medico.",
        "cita_id": cita_id
    }


# =============================================================================
# Cancelar cita (solo doctor autenticado, solo sus citas)
# =============================================================================
@router.put("/cancelar/{cita_id}")
async def cancelar_cita_doctor(
    cita_id: int,
    notas: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """Cancelar una cita asignada al doctor autenticado."""
    doctor_id = user["id"]  # Extraido del token JWT

    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Esta cita no es suya")

    if cita.estado == "cancelada":
        raise HTTPException(status_code=400, detail="La cita ya esta cancelada")

    if cita.estado == "completada":
        raise HTTPException(status_code=400, detail="No se puede cancelar una cita completada")

    data = CitaUpdateEstado(estado="cancelada", notas=notas)
    await cita_service.actualizar_estado(session, cita_id, data)

    logger.info("[DOCTOR-PORTAL] Dr.#%s cancelo cita #%s", doctor_id, cita_id)
    return {"mensaje": "Cita cancelada exitosamente", "cita_id": cita_id}
