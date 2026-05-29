"""
cita.me — CRUD de Doctores (protegido con JWT)

Permisos:
  - admin / administrativo: listar, crear, obtener, actualizar
  - admin: desactivar (soft-delete)
  - doctor: solo obtener su propio perfil
  - paciente: listar (para seleccionar al pedir cita)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_session
from dependencies import get_current_user, require_role, require_any_role
from models import Doctor
from schemas import DoctorCreate, DoctorResponse
from security import get_password_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doctores", tags=["Doctores"])


# =============================================================================
# Listar doctores activos (cualquier usuario autenticado)
# Solo admin/administrativo ven los inactivos via filtro
# =============================================================================
@router.get("/", response_model=List[DoctorResponse])
async def listar_doctores(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Listar doctores. Admin y administrativo ven todos (activos e inactivos).
    Doctor y paciente solo ven los activos.
    """
    if user["rol"] in ("admin", "administrativo"):
        stmt = select(Doctor).order_by(Doctor.apellido, Doctor.nombre)
    else:
        stmt = select(Doctor).where(Doctor.activo == True).order_by(Doctor.apellido, Doctor.nombre)

    result = await session.execute(stmt)
    return result.scalars().all()


# =============================================================================
# Obtener un doctor por ID (cualquier usuario autenticado)
# =============================================================================
@router.get("/{doctor_id}", response_model=DoctorResponse)
async def obtener_doctor(
    doctor_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Obtener un doctor por su ID. Requiere autenticacion."""
    doctor = await session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # Un doctor inactivo solo es visible para admin/administrativo
    if not doctor.activo and user["rol"] not in ("admin", "administrativo"):
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    return doctor


# =============================================================================
# Crear doctor (admin, administrativo)
# =============================================================================
@router.post("/", response_model=DoctorResponse, status_code=201)
async def crear_doctor(
    data: DoctorCreate,
    user: dict = Depends(require_any_role("admin", "administrativo")),
    session: AsyncSession = Depends(get_session),
):
    """Registrar un nuevo doctor. Requiere admin o administrativo."""
    stmt = select(Doctor).where(Doctor.email == data.email)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Ya existe un doctor con ese email",
        )

    nuevo = Doctor(
        nombre=data.nombre,
        apellido=data.apellido,
        especialidad=data.especialidad,
        email=data.email,
        telefono=data.telefono,
        activo=True,
        password_hash=get_password_hash(data.contrasena or "1234"),
    )
    session.add(nuevo)
    await session.flush()

    logger.info(
        "[DOCTOR] %s #%s creo doctor #%s (%s)",
        user["rol"], user["id"], nuevo.id, nuevo.email,
    )
    return nuevo


# =============================================================================
# Actualizar doctor (admin, administrativo)
# =============================================================================
@router.put("/{doctor_id}", response_model=DoctorResponse)
async def actualizar_doctor(
    doctor_id: int,
    data: DoctorCreate,
    user: dict = Depends(require_any_role("admin", "administrativo")),
    session: AsyncSession = Depends(get_session),
):
    """Actualizar datos de un doctor. Requiere admin o administrativo."""
    doctor = await session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # Verificar unicidad de email si cambio
    if data.email != doctor.email:
        stmt = select(Doctor).where(Doctor.email == data.email)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email ya registrado por otro doctor")

    doctor.nombre = data.nombre
    doctor.apellido = data.apellido
    doctor.especialidad = data.especialidad
    doctor.email = data.email
    doctor.telefono = data.telefono

    if data.contrasena:
        doctor.password_hash = get_password_hash(data.contrasena)

    await session.flush()
    logger.info("[DOCTOR] %s #%s actualizo doctor #%s", user["rol"], user["id"], doctor_id)
    return doctor


# =============================================================================
# Desactivar doctor — soft-delete (solo admin)
# =============================================================================
@router.delete("/{doctor_id}")
async def desactivar_doctor(
    doctor_id: int,
    user: dict = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Desactivar un doctor (soft-delete). Solo admin."""
    doctor = await session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    doctor.activo = False
    await session.flush()

    logger.info("[DOCTOR] Admin #%s desactivo doctor #%s", user["id"], doctor_id)
    return {"mensaje": "Doctor desactivado exitosamente", "id": doctor_id}