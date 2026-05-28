"""
cita.me — CRUD de Administrativos
Solo el rol "admin" puede gestionar administrativos.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import require_role
from models import Administrativo
from schemas import AdministrativoCreate, AdministrativoResponse
from security import get_password_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/administrativos", tags=["Administrativos"])


# =============================================================================
# Crear administrativo (solo admin)
# =============================================================================
@router.post("/", response_model=AdministrativoResponse, status_code=201)
async def crear_administrativo(
    data: AdministrativoCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Crear un nuevo usuario administrativo. Solo admin."""
    # Verificar email unico
    stmt = select(Administrativo).where(Administrativo.email == data.email)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un administrativo con ese email")

    admin = Administrativo(
        nombre=data.nombre,
        apellido=data.apellido,
        email=data.email,
        telefono=data.telefono,
        password_hash=get_password_hash(data.contrasena),
        activo=True,
    )
    session.add(admin)
    await session.flush()

    logger.info("[ADMINISTRATIVO] Creado: #%s - %s %s", admin.id, admin.nombre, admin.apellido)
    return admin


# =============================================================================
# Listar administrativos activos (solo admin)
# =============================================================================
@router.get("/", response_model=list[AdministrativoResponse])
async def listar_administrativos(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Listar todos los administrativos activos. Solo admin."""
    stmt = select(Administrativo).where(Administrativo.activo == True).order_by(Administrativo.creado_en.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


# =============================================================================
# Obtener un administrativo por ID (solo admin)
# =============================================================================
@router.get("/{admin_id}", response_model=AdministrativoResponse)
async def obtener_administrativo(
    admin_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Obtener un administrativo por su ID. Solo admin."""
    admin = await session.get(Administrativo, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrativo no encontrado")
    return admin


# =============================================================================
# Actualizar administrativo (solo admin)
# =============================================================================
@router.put("/{admin_id}", response_model=AdministrativoResponse)
async def actualizar_administrativo(
    admin_id: int,
    data: AdministrativoCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Actualizar datos de un administrativo. Solo admin."""
    admin = await session.get(Administrativo, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrativo no encontrado")

    # Verificar email unico (si cambio)
    if data.email != admin.email:
        stmt = select(Administrativo).where(Administrativo.email == data.email)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email ya registrado")

    admin.nombre = data.nombre
    admin.apellido = data.apellido
    admin.email = data.email
    admin.telefono = data.telefono
    # Solo actualizar password si se proporciona una nueva
    if data.contrasena and data.contrasena != "":
        admin.password_hash = get_password_hash(data.contrasena)

    await session.flush()
    logger.info("[ADMINISTRATIVO] Actualizado: #%s", admin.id)
    return admin


# =============================================================================
# Desactivar (soft-delete) administrativo (solo admin)
# =============================================================================
@router.delete("/{admin_id}")
async def desactivar_administrativo(
    admin_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Desactivar un administrativo (soft-delete). Solo admin."""
    admin = await session.get(Administrativo, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrativo no encontrado")

    admin.activo = False
    await session.flush()

    logger.info("[ADMINISTRATIVO] Desactivado: #%s", admin.id)
    return {"mensaje": "Administrativo desactivado exitosamente", "id": admin_id}
