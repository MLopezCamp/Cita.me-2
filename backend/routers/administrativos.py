"""
cita.me — Administrativos: CRUD (admin) + Portal propio (administrativo)

Permisos:
  - admin: CRUD completo sobre administrativos
  - administrativo: ver y actualizar su propio perfil
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import get_current_user, require_role
from models import Administrativo, Cita, Doctor, Paciente
from schemas import AdministrativoCreate, AdministrativoResponse
from security import get_password_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/administrativos", tags=["Administrativos"])


# =============================================================================
# CRUD — Solo admin
# =============================================================================

@router.post("/", response_model=AdministrativoResponse, status_code=201)
async def crear_administrativo(
    data: AdministrativoCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Crear un nuevo usuario administrativo. Solo admin."""
    stmt = select(Administrativo).where(Administrativo.email == data.email)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un administrativo con ese email")

    nuevo = Administrativo(
        nombre=data.nombre,
        apellido=data.apellido,
        email=data.email,
        telefono=data.telefono,
        password_hash=get_password_hash(data.contrasena),
        activo=True,
    )
    session.add(nuevo)
    await session.flush()

    logger.info("[ADMIN] Creado administrativo #%s - %s %s", nuevo.id, nuevo.nombre, nuevo.apellido)
    return nuevo


@router.get("/", response_model=list[AdministrativoResponse])
async def listar_administrativos(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Listar todos los administrativos. Solo admin."""
    stmt = select(Administrativo).order_by(Administrativo.apellido, Administrativo.nombre)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{admin_id}", response_model=AdministrativoResponse)
async def obtener_administrativo(
    admin_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Obtener un administrativo por ID. Solo admin."""
    admin = await session.get(Administrativo, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrativo no encontrado")
    return admin


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

    if data.email != admin.email:
        stmt = select(Administrativo).where(Administrativo.email == data.email)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email ya registrado")

    admin.nombre = data.nombre
    admin.apellido = data.apellido
    admin.email = data.email
    admin.telefono = data.telefono
    if data.contrasena:
        admin.password_hash = get_password_hash(data.contrasena)

    await session.flush()
    logger.info("[ADMIN] Actualizado administrativo #%s", admin.id)
    return admin


@router.delete("/{admin_id}")
async def desactivar_administrativo(
    admin_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Desactivar (soft-delete) un administrativo. Solo admin."""
    admin = await session.get(Administrativo, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrativo no encontrado")

    admin.activo = False
    await session.flush()

    logger.info("[ADMIN] Desactivado administrativo #%s", admin_id)
    return {"mensaje": "Administrativo desactivado exitosamente", "id": admin_id}


# =============================================================================
# PORTAL PROPIO — El administrativo autenticado gestiona su panel
# =============================================================================

@router.get("/portal/perfil", response_model=AdministrativoResponse)
async def mi_perfil(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("administrativo")),
):
    """El administrativo autenticado consulta su propio perfil."""
    admin = await session.get(Administrativo, user["id"])
    if not admin:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return admin


@router.get("/portal/citas")
async def mis_citas_gestion(
    estado: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("administrativo")),
):
    """
    El administrativo lista todas las citas del sistema para gestionarlas.
    Puede filtrar por estado: pendiente, confirmada, cancelada, completada.
    """
    stmt = select(Cita)
    if estado:
        stmt = stmt.where(Cita.estado == estado)
    stmt = stmt.order_by(Cita.fecha.desc(), Cita.hora.desc())

    result = await session.execute(stmt)
    citas = result.scalars().all()

    respuesta = []
    for c in citas:
        paciente = await session.get(Paciente, c.paciente_id)
        doctor = await session.get(Doctor, c.doctor_id)
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
            "doctor_id": c.doctor_id,
            "doctor_nombre": f"Dr. {doctor.nombre} {doctor.apellido}" if doctor else "Desconocido",
            "doctor_especialidad": doctor.especialidad if doctor else "",
        })

    return respuesta


@router.get("/portal/doctores")
async def listar_doctores_portal(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("administrativo")),
):
    """El administrativo lista los doctores activos."""
    stmt = select(Doctor).where(Doctor.activo == True).order_by(Doctor.apellido)
    result = await session.execute(stmt)
    doctores = result.scalars().all()
    return [
        {
            "id": d.id,
            "nombre": f"Dr. {d.nombre} {d.apellido}",
            "especialidad": d.especialidad,
            "email": d.email,
            "telefono": d.telefono,
        }
        for d in doctores
    ]


@router.get("/portal/pacientes")
async def listar_pacientes_portal(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("administrativo")),
):
    """El administrativo lista todos los pacientes."""
    stmt = select(Paciente).order_by(Paciente.apellido, Paciente.nombre)
    result = await session.execute(stmt)
    pacientes = result.scalars().all()
    return [
        {
            "id": p.id,
            "nombre": f"{p.nombre} {p.apellido}",
            "documento": p.documento,
            "email": p.email,
            "telefono": p.telefono,
        }
        for p in pacientes
    ]