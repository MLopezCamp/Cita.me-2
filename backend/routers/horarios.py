"""Endpoints de horarios de doctores."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import Horario, Doctor
from schemas import HorarioCreate, HorarioResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/horarios", tags=["Horarios"])

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


@router.post("/", response_model=HorarioResponse, status_code=201)
async def crear_horario(data: HorarioCreate, session: AsyncSession = Depends(get_session)):
    """Asignar un horario de atención a un doctor."""
    doctor = await session.get(Doctor, data.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # Verificar que no solape con horario existente
    stmt = select(Horario).where(
        and_(
            Horario.doctor_id == data.doctor_id,
            Horario.dia_semana == data.dia_semana,
            Horario.activo == True,
        )
    )
    resultado = await session.execute(stmt)
    existentes = resultado.scalars().all()

    for ex in existentes:
        if data.hora_inicio < ex.hora_fin and data.hora_fin > ex.hora_inicio:
            raise HTTPException(
                status_code=400,
                detail=f"El horario se solapa con un horario existente "
                       f"({ex.hora_inicio} - {ex.hora_fin} los {DIAS[data.dia_semana]})"
            )

    horario = Horario(**data.model_dump())
    session.add(horario)
    await session.flush()

    logger.info(f"[HORARIO] Creado: doctor={data.doctor_id}, {DIAS[data.dia_semana]} "
                f"{data.hora_inicio}-{data.hora_fin}")
    return horario


@router.get("/doctor/{doctor_id}", response_model=list[HorarioResponse])
async def listar_horarios_doctor(doctor_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener todos los horarios de un doctor."""
    stmt = select(Horario).where(
        and_(Horario.doctor_id == doctor_id, Horario.activo == True)
    ).order_by(Horario.dia_semana, Horario.hora_inicio)
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())