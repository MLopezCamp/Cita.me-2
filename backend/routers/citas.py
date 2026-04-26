"""
Endpoints de citas médicas.
Usa el servicio con locking distribuido y comunicación async.
"""
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from schemas import CitaCreate, CitaResponse, CitaUpdateEstado, CitaDetalle
from services import cita_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/citas", tags=["Citas"])


@router.post("/", response_model=CitaResponse, status_code=201)
async def crear_cita(data: CitaCreate, session: AsyncSession = Depends(get_session)):
    """
    Crear una nueva cita médica.

    Este endpoint demuestra:
    - Locking distribuido con Redis (previene doble reserva)
    - Publicación de eventos a RabbitMQ (comunicación async)
    - Invalidación de cache
    """
    try:
        cita = await cita_service.crear_cita(session, data)
        return cita
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/{cita_id}")
async def obtener_cita(cita_id: int, session: AsyncSession = Depends(get_session)):
    """
    Obtener detalle de una cita por ID.

    Demuestra: cache en Redis para respuestas frecuentes.
    """
    data = await cita_service.obtener_cita(session, cita_id)
    if not data:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return data


@router.get("/", response_model=list[CitaResponse])
async def listar_citas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Listar todas las citas con paginación."""
    return await cita_service.listar_citas(session, skip, limit)


@router.get("/paciente/{paciente_id}", response_model=list[CitaResponse])
async def citas_por_paciente(paciente_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener todas las citas de un paciente."""
    return await cita_service.listar_citas_paciente(session, paciente_id)


@router.get("/doctor/{doctor_id}", response_model=list[CitaResponse])
async def citas_por_doctor(doctor_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener todas las citas de un doctor."""
    return await cita_service.listar_citas_doctor(session, doctor_id)


@router.get("/disponibles/{doctor_id}")
async def horarios_disponibles(
    doctor_id: int,
    fecha: date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
):
    """
    Obtener horarios disponibles de un doctor en una fecha.

    Demuestra: cache en Redis + cálculo de slots.
    """
    disponibles = await cita_service.obtener_disponibles(session, doctor_id, fecha)
    return {"doctor_id": doctor_id, "fecha": str(fecha), "slots": disponibles}


@router.put("/{cita_id}/estado", response_model=CitaResponse)
async def actualizar_estado_cita(
    cita_id: int,
    data: CitaUpdateEstado,
    session: AsyncSession = Depends(get_session),
):
    """
    Actualizar el estado de una cita (confirmar, cancelar, completar).

    Demuestra: publicación de eventos a RabbitMQ según el cambio de estado.
    """
    cita = await cita_service.actualizar_estado(session, cita_id, data)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita