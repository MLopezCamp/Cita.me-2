"""
cita.me — CRUD de Pacientes (protegido con JWT)

Permisos:
  - admin / administrativo: listar, crear, obtener, actualizar
  - paciente: solo obtener y actualizar sus propios datos
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_session
from dependencies import get_current_user, require_any_role
from models import Paciente
from schemas import PacienteCreate, PacienteResponse
from security import get_password_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def _solo_admin_o_administrativo(user: dict):
    """Lanza 403 si el usuario no es admin ni administrativo."""
    if user["rol"] not in ("admin", "administrativo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol admin o administrativo",
        )


# =============================================================================
# Listar pacientes (admin, administrativo)
# =============================================================================
@router.get("/", response_model=List[PacienteResponse])
async def listar_pacientes(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Listar todos los pacientes registrados. Requiere admin o administrativo."""
    _solo_admin_o_administrativo(user)
    stmt = select(Paciente).order_by(Paciente.apellido, Paciente.nombre)
    result = await session.execute(stmt)
    return result.scalars().all()


# =============================================================================
# Obtener un paciente por ID (admin, administrativo, o el propio paciente)
# =============================================================================
@router.get("/{paciente_id}", response_model=PacienteResponse)
async def obtener_paciente(
    paciente_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Obtener un paciente por ID.
    El propio paciente solo puede ver sus propios datos.
    """
    rol = user["rol"]

    if rol == "paciente":
        # Un paciente solo puede verse a si mismo
        if user["id"] != paciente_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver este perfil",
            )
    elif rol not in ("admin", "administrativo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol admin, administrativo o paciente",
        )

    paciente = await session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    return paciente


# =============================================================================
# Crear paciente (admin, administrativo)
# =============================================================================
@router.post("/", response_model=PacienteResponse, status_code=201)
async def crear_paciente(
    data: PacienteCreate,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Registrar un nuevo paciente. Requiere admin o administrativo."""
    _solo_admin_o_administrativo(user)

    # Verificar unicidad de email y documento
    stmt = select(Paciente).where(
        (Paciente.email == data.email) | (Paciente.documento == data.documento)
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Ya existe un paciente con ese email o documento",
        )

    nuevo = Paciente(
        nombre=data.nombre,
        apellido=data.apellido,
        documento=data.documento,
        email=data.email,
        telefono=data.telefono,
        fecha_nacimiento=data.fecha_nacimiento,
        password_hash=get_password_hash(data.contrasena or "1234"),
    )
    session.add(nuevo)
    await session.flush()

    logger.info(
        "[PACIENTE] %s #%s creo paciente #%s (%s)",
        user["rol"], user["id"], nuevo.id, nuevo.documento,
    )
    return nuevo


# =============================================================================
# Actualizar paciente (admin, administrativo, o el propio paciente)
# =============================================================================
@router.put("/{paciente_id}", response_model=PacienteResponse)
async def actualizar_paciente(
    paciente_id: int,
    data: PacienteCreate,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Actualizar datos de un paciente.
    El propio paciente solo puede actualizar sus propios datos.
    """
    rol = user["rol"]

    if rol == "paciente":
        if user["id"] != paciente_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para modificar este perfil",
            )
    elif rol not in ("admin", "administrativo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol admin, administrativo o paciente",
        )

    paciente = await session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Verificar unicidad de email/documento si cambiaron
    if data.email != paciente.email or data.documento != paciente.documento:
        stmt = select(Paciente).where(
            ((Paciente.email == data.email) | (Paciente.documento == data.documento))
            & (Paciente.id != paciente_id)
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Email o documento ya registrado por otro paciente",
            )

    paciente.nombre = data.nombre
    paciente.apellido = data.apellido
    paciente.documento = data.documento
    paciente.email = data.email
    paciente.telefono = data.telefono
    paciente.fecha_nacimiento = data.fecha_nacimiento

    if data.contrasena:
        paciente.password_hash = get_password_hash(data.contrasena)

    await session.flush()
    logger.info("[PACIENTE] %s #%s actualizo paciente #%s", rol, user["id"], paciente_id)
    return paciente