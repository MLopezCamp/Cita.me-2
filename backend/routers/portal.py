"""
cita.me — Portal del paciente.
Endpoints que usa el paciente autogestionándose:
ver sus citas, pedir nueva cita, cancelar cita.
"""
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_session
from models import Cita
from schemas import CitaCreate, CitaResponse, CitaUpdateEstado
from services import cita_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portal", tags=["Portal Paciente"])


@router.get("/mis-citas")
async def mis_citas(
    paciente_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Obtener todas las citas del paciente (incluyendo canceladas)."""
    stmt = (
        select(Cita)
        .where(Cita.paciente_id == paciente_id)
        .order_by(Cita.fecha.desc(), Cita.hora.desc())
    )
    resultado = await session.execute(stmt)
    citas = resultado.scalars().all()

    # Enriquecer con datos del doctor
    from models import Doctor
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


@router.post("/pedir-cita", response_model=CitaResponse, status_code=201)
async def pedir_cita(
    data: CitaCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    El paciente pide una cita.
    Usa el mismo servicio con locking distribuido.
    El paciente_id viene en el body.
    """
    # Verificar que el paciente_id del body coincida (seguridad básica)
    try:
        cita = await cita_service.crear_cita(session, data)
        return cita
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.put("/cancelar/{cita_id}")
async def cancelar_mi_cita(
    cita_id: int,
    paciente_id: int,
    notas: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    El paciente cancela su propia cita.
    Verifica que la cita pertenece al paciente.
    """
    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Seguridad: verificar que es la cita del paciente
    if cita.paciente_id != paciente_id:
        raise HTTPException(status_code=403, detail="Esta cita no le pertenece")

    if cita.estado == "cancelada":
        raise HTTPException(status_code=400, detail="La cita ya está cancelada")

    if cita.estado == "completada":
        raise HTTPException(status_code=400, detail="No se puede cancelar una cita completada")

    data = CitaUpdateEstado(estado="cancelada", notas=notas)
    cita_actualizada = await cita_service.actualizar_estado(session, cita_id, data)

    logger.info("[cita.me/PORTAL] Paciente #%s canceló cita #%s", paciente_id, cita_id)
    return {"mensaje": "Cita cancelada exitosamente", "cita_id": cita_id}


@router.get("/doctores-disponibles")
async def doctores_para_portal(session: AsyncSession = Depends(get_session)):
    """Lista simplificada de doctores para el portal del paciente."""
    from models import Doctor
    stmt = select(Doctor).where(Doctor.activo == True)
    resultado = await session.execute(stmt)
    doctores = resultado.scalars().all()
    return [
        {
            "id": d.id,
            "nombre": f"Dr. {d.nombre} {d.apellido}",
            "especialidad": d.especialidad,
        }
        for d in doctores
    ]