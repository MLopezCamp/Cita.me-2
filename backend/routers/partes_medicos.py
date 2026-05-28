"""
cita.me — Partes Medicos
Solo los doctores pueden crear y ver partes medicos de sus propias citas.
Los admins tambien pueden ver todos los partes medicos.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import get_current_user, require_role, require_any_role
from models import ParteMedico, Cita
from schemas import ParteMedicoCreate, ParteMedicoResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/partes-medicos", tags=["Partes Medicos"])


# =============================================================================
# Crear parte medico (solo doctor, solo sus citas completadas)
# =============================================================================
@router.post("/", response_model=ParteMedicoResponse, status_code=201)
async def crear_parte_medico(
    data: ParteMedicoCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """
    El doctor registra un parte medico para una cita completada.
    Solo puede registrar partes de citas donde el es el doctor asignado.
    """
    doctor_id = user["id"]

    # Verificar que la cita existe y pertenece al doctor
    cita = await session.get(Cita, data.cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.doctor_id != doctor_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puede registrar partes medicos de sus propias citas"
        )

    # Verificar que la cita esta completada
    if cita.estado != "completada":
        raise HTTPException(
            status_code=400,
            detail="La cita debe estar en estado 'completada' para registrar un parte medico"
        )

    # Verificar que no exista ya un parte medico para esta cita
    stmt = select(ParteMedico).where(ParteMedico.cita_id == data.cita_id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Ya existe un parte medico para esta cita"
        )

    parte = ParteMedico(
        cita_id=data.cita_id,
        doctor_id=doctor_id,
        diagnostico=data.diagnostico,
        tratamiento=data.tratamiento,
        observaciones=data.observaciones,
    )
    session.add(parte)
    await session.flush()

    logger.info("[PARTE_MEDICO] Dr.#%s registro parte para cita #%s", doctor_id, data.cita_id)
    return parte


# =============================================================================
# Obtener parte medico por cita (doctor: solo suyo, admin: cualquiera)
# =============================================================================
@router.get("/cita/{cita_id}", response_model=ParteMedicoResponse)
async def obtener_parte_por_cita(
    cita_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("doctor", "admin")),
):
    """Obtener el parte medico asociado a una cita especifica."""
    stmt = select(ParteMedico).where(ParteMedico.cita_id == cita_id)
    result = await session.execute(stmt)
    parte = result.scalar_one_or_none()

    if not parte:
        raise HTTPException(status_code=404, detail="Parte medico no encontrado")

    # Si es doctor, verificar que sea su parte
    if user["rol"] == "doctor" and parte.doctor_id != user["id"]:
        raise HTTPException(status_code=403, detail="No tiene permiso para ver este parte medico")

    return parte


# =============================================================================
# Listar partes medicos del doctor autenticado
# =============================================================================
@router.get("/mis-partes", response_model=list[ParteMedicoResponse])
async def mis_partes_medicos(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """Listar todos los partes medicos registrados por el doctor autenticado."""
    stmt = select(ParteMedico).where(
        ParteMedico.doctor_id == user["id"]
    ).order_by(ParteMedico.creado_en.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


# =============================================================================
# Obtener parte medico por ID (doctor: solo suyo, admin: cualquiera)
# =============================================================================
@router.get("/{parte_id}", response_model=ParteMedicoResponse)
async def obtener_parte_medico(
    parte_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("doctor", "admin")),
):
    """Obtener un parte medico por su ID."""
    parte = await session.get(ParteMedico, parte_id)
    if not parte:
        raise HTTPException(status_code=404, detail="Parte medico no encontrado")

    # Si es doctor, verificar que sea su parte
    if user["rol"] == "doctor" and parte.doctor_id != user["id"]:
        raise HTTPException(status_code=403, detail="No tiene permiso para ver este parte medico")

    return parte


# =============================================================================
# Actualizar parte medico (solo doctor, solo sus propios)
# =============================================================================
@router.put("/{parte_id}", response_model=ParteMedicoResponse)
async def actualizar_parte_medico(
    parte_id: int,
    data: ParteMedicoCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("doctor")),
):
    """Actualizar un parte medico. Solo el doctor que lo creo puede editarlo."""
    parte = await session.get(ParteMedico, parte_id)
    if not parte:
        raise HTTPException(status_code=404, detail="Parte medico no encontrado")

    if parte.doctor_id != user["id"]:
        raise HTTPException(status_code=403, detail="Solo puede editar sus propios partes medicos")

    parte.diagnostico = data.diagnostico
    parte.tratamiento = data.tratamiento
    parte.observaciones = data.observaciones

    await session.flush()
    logger.info("[PARTE_MEDICO] Dr.#%s actualizo parte #%s", user["id"], parte_id)
    return parte
