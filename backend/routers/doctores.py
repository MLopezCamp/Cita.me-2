"""Endpoints de doctores."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import Doctor
from schemas import DoctorCreate, DoctorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doctores", tags=["Doctores"])


@router.post("/", response_model=DoctorResponse, status_code=201)
async def crear_doctor(data: DoctorCreate, session: AsyncSession = Depends(get_session)):
    """Registrar un nuevo doctor en el sistema."""
    stmt = select(Doctor).where(Doctor.email == data.email)
    resultado = await session.execute(stmt)
    if resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un doctor con ese email")

    doctor = Doctor(**data.model_dump())
    session.add(doctor)
    await session.flush()

    logger.info(f"[DOCTOR] Creado: #{doctor.id} - Dr. {doctor.nombre} {doctor.apellido} ({doctor.especialidad})")
    return doctor


@router.get("/", response_model=list[DoctorResponse])
async def listar_doctores(skip: int = 0, limit: int = 50, session: AsyncSession = Depends(get_session)):
    """Obtener lista de doctores."""
    stmt = select(Doctor).where(Doctor.activo == True).offset(skip).limit(limit)
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def obtener_doctor(doctor_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener un doctor por su ID."""
    doctor = await session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    return doctor