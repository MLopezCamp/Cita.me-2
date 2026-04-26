"""Endpoints de pacientes."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import Paciente
from schemas import PacienteCreate, PacienteResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post("/", response_model=PacienteResponse, status_code=201)
async def crear_paciente(data: PacienteCreate, session: AsyncSession = Depends(get_session)):
    """Registrar un nuevo paciente en el sistema."""
    # Verificar documento único
    stmt = select(Paciente).where(Paciente.documento == data.documento)
    resultado = await session.execute(stmt)
    if resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un paciente con ese documento")

    # Verificar email único
    stmt = select(Paciente).where(Paciente.email == data.email)
    resultado = await session.execute(stmt)
    if resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un paciente con ese email")

    paciente = Paciente(**data.model_dump())
    session.add(paciente)
    await session.flush()

    logger.info(f"[PACIENTE] Creado: #{paciente.id} - {paciente.nombre} {paciente.apellido}")
    return paciente


@router.get("/", response_model=list[PacienteResponse])
async def listar_pacientes(skip: int = 0, limit: int = 50, session: AsyncSession = Depends(get_session)):
    """Obtener lista de pacientes con paginación."""
    stmt = select(Paciente).offset(skip).limit(limit)
    resultado = await session.execute(stmt)
    return list(resultado.scalars().all())


@router.get("/{paciente_id}", response_model=PacienteResponse)
async def obtener_paciente(paciente_id: int, session: AsyncSession = Depends(get_session)):
    """Obtener un paciente por su ID."""
    paciente = await session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


@router.get("/documento/{documento}", response_model=PacienteResponse)
async def buscar_por_documento(documento: str, session: AsyncSession = Depends(get_session)):
    """Buscar paciente por número de documento."""
    stmt = select(Paciente).where(Paciente.documento == documento)
    resultado = await session.execute(stmt)
    paciente = resultado.scalar_one_or_none()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente