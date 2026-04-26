"""
cita.me — Portal del doctor.
Ver sus citas, completar citas con notas.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from database import get_session
from models import Cita, Doctor, Paciente
from schemas import CitaUpdateEstado
from services import cita_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doctor-portal", tags=["Portal Doctor"])


@router.get("/mis-citas")
async def mis_citas(
    doctor_id: int,
    estado: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Citas del doctor, opcionalmente filtradas por estado."""
    stmt = select(Cita).where(Cita.doctor_id == doctor_id)

    if estado:
        stmt = stmt.where(Cita.estado == estado)

    stmt = stmt.order_by(Cita.fecha.desc(), Cita.hora.desc())
    resultado = await session.execute(stmt)
    citas = resultado.scalars().all()

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


@router.get("/cita/{cita_id}")
async def detalle_cita(
    cita_id: int,
    doctor_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Detalle de una cita del doctor."""
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


@router.put("/completar/{cita_id}")
async def completar_cita(
    cita_id: int,
    doctor_id: int,
    notas: str,
    session: AsyncSession = Depends(get_session),
):
    """El doctor marca una cita como completada y agrega notas."""
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

    logger.info("[cita.me/DOCTOR] Dr.#%s completó cita #%s", doctor_id, cita_id)
    return {"mensaje": "Cita completada exitosamente", "cita_id": cita_id}


@router.put("/confirmar/{cita_id}")
async def confirmar_cita(
    cita_id: int,
    doctor_id: int,
    session: AsyncSession = Depends(get_session),
):
    """El doctor confirma una cita pendiente."""
    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if cita.doctor_id != doctor_id:
        raise HTTPException(status_code=403, detail="Esta cita no es suya")
    if cita.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar citas pendientes")

    data = CitaUpdateEstado(estado="confirmada")
    await cita_service.actualizar_estado(session, cita_id, data)

    logger.info("[cita.me/DOCTOR] Dr.#%s confirmó cita #%s", doctor_id, cita_id)
    return {"mensaje": "Cita confirmada", "cita_id": cita_id}