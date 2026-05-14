"""
cita.me — Endpoints de citas.
El request_id se genera aquí con uuid4 y viaja por toda la cadena.
"""
import logging
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from schemas import CitaCreate, CitaResponse, CitaUpdateEstado
from services import cita_service

logger = logging.getLogger("api")
router = APIRouter(prefix="/citas", tags=["Citas"])


@router.post("/", response_model=CitaResponse, status_code=201)
async def crear_cita(data: CitaCreate, session: AsyncSession = Depends(get_session)):
    # Generar el request_id que viajara por toda la cadena
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "[API] [%s] Peticion recibida: POST /citas",
        request_id,
        extra={"service": "api", "request_id": request_id},
    )

    try:
        cita = await cita_service.crear_cita(session, data, request_id=request_id)
        return cita
    except ValueError as e:
        logger.error(
            "[API] [%s] Error validacion: %s",
            request_id, str(e),
            extra={"service": "api", "request_id": request_id},
        )
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/{cita_id}")
async def obtener_cita(cita_id: int, session: AsyncSession = Depends(get_session)):
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
    return await cita_service.listar_citas(session, skip, limit)


@router.get("/paciente/{paciente_id}", response_model=list[CitaResponse])
async def citas_por_paciente(paciente_id: int, session: AsyncSession = Depends(get_session)):
    return await cita_service.listar_citas_paciente(session, paciente_id)


@router.get("/doctor/{doctor_id}", response_model=list[CitaResponse])
async def citas_por_doctor(doctor_id: int, session: AsyncSession = Depends(get_session)):
    return await cita_service.listar_citas_doctor(session, doctor_id)


@router.get("/disponibles/{doctor_id}")
async def horarios_disponibles(
    doctor_id: int,
    fecha: date = Query(..., description="Fecha YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
):
    disponibles = await cita_service.obtener_disponibles(session, doctor_id, fecha)
    return {"doctor_id": doctor_id, "fecha": str(fecha), "slots": disponibles}


@router.put("/{cita_id}/estado", response_model=CitaResponse)
async def actualizar_estado_cita(
    cita_id: int,
    data: CitaUpdateEstado,
    session: AsyncSession = Depends(get_session),
):
    cita = await cita_service.actualizar_estado(session, cita_id, data)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita