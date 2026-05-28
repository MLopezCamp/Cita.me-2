"""
cita.me — Endpoints de citas (protegidos con JWT)

Permisos por rol:
  - admin: CRUD completo
  - administrativo: crear, confirmar, cancelar
  - doctor: confirmar, completar, cancelar (solo sus citas)
  - paciente: crear, cancelar propias (via /portal)
"""
import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import get_current_user, require_role, require_any_role
from models import Cita
from schemas import CitaCreate, CitaResponse, CitaUpdateEstado
from services import cita_service

logger = logging.getLogger("api")
router = APIRouter(prefix="/citas", tags=["Citas"])


# =============================================================================
# Crear cita (admin, administrativo)
# =============================================================================
@router.post("/", response_model=CitaResponse, status_code=201)
async def crear_cita(
    data: CitaCreate,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "administrativo")),
):
    """Crear una nueva cita. Requiere rol admin o administrativo."""
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "[API] [%s] POST /citas por %s #%s",
        request_id, user["rol"], user["id"]
    )

    try:
        cita = await cita_service.crear_cita(session, data, request_id=request_id)
        return cita
    except ValueError as e:
        logger.error("[API] [%s] Error validacion: %s", request_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


# =============================================================================
# Listar TODAS las citas (solo admin)
# =============================================================================
@router.get("/", response_model=list[CitaResponse])
async def listar_citas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Listar todas las citas del sistema. Solo admin."""
    return await cita_service.listar_citas(session, skip, limit)


# =============================================================================
# Obtener una cita por ID (admin, doctor si es suya, admin puede todas)
# =============================================================================
@router.get("/{cita_id}")
async def obtener_cita(
    cita_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """Obtener detalle de una cita. Admin ve todas; doctor solo las suyas."""
    data = await cita_service.obtener_cita(session, cita_id)
    if not data:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Doctor solo puede ver sus citas
    if user["rol"] == "doctor" and data["doctor_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="No tiene permiso para ver esta cita")

    return data


# =============================================================================
# Citas por paciente (admin, o el propio paciente via /portal)
# =============================================================================
@router.get("/paciente/{paciente_id}", response_model=list[CitaResponse])
async def citas_por_paciente(
    paciente_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Listar citas de un paciente. Solo admin."""
    return await cita_service.listar_citas_paciente(session, paciente_id)


# =============================================================================
# Citas por doctor (admin, o el propio doctor via /doctor-portal)
# =============================================================================
@router.get("/doctor/{doctor_id}", response_model=list[CitaResponse])
async def citas_por_doctor(
    doctor_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Listar citas de un doctor. Solo admin."""
    return await cita_service.listar_citas_doctor(session, doctor_id)


# =============================================================================
# Horarios disponibles (cualquier usuario autenticado)
# =============================================================================
@router.get("/disponibles/{doctor_id}")
async def horarios_disponibles(
    doctor_id: int,
    fecha: date = Query(..., description="Fecha YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """Consultar horarios disponibles de un doctor. Requiere autenticacion."""
    disponibles = await cita_service.obtener_disponibles(session, doctor_id, fecha)
    return {
        "doctor_id": doctor_id,
        "fecha": str(fecha),
        "slots": disponibles
    }


# =============================================================================
# Actualizar estado de cita (roles: admin, doctor, administrativo)
# =============================================================================
@router.put("/{cita_id}/estado", response_model=CitaResponse)
async def actualizar_estado_cita(
    cita_id: int,
    data: CitaUpdateEstado,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_any_role("admin", "doctor", "administrativo")),
):
    """
    Actualizar el estado de una cita.

    **Permisos por accion:**
    - confirmar: admin, doctor (sus citas), administrativo
    - cancelar: admin, doctor (sus citas), administrativo
    - completar: admin, doctor (sus citas)
    """
    # Verificar que la cita existe
    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    rol = user["rol"]

    # Doctor solo puede operar sobre sus citas
    if rol == "doctor" and cita.doctor_id != user["id"]:
        raise HTTPException(status_code=403, detail="No tiene permiso sobre esta cita")

    # Administrativo NO puede completar citas
    if rol == "administrativo" and data.estado == "completada":
        raise HTTPException(
            status_code=403,
            detail="Los administrativos no pueden completar citas"
        )

    # Validar transiciones de estado
    if data.estado == "confirmada" and cita.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar citas pendientes")

    if data.estado == "completada":
        if cita.estado == "cancelada":
            raise HTTPException(status_code=400, detail="No se puede completar una cita cancelada")
        if cita.estado == "completada":
            raise HTTPException(status_code=400, detail="La cita ya fue completada")

    if data.estado == "cancelada":
        if cita.estado == "cancelada":
            raise HTTPException(status_code=400, detail="La cita ya esta cancelada")
        if cita.estado == "completada":
            raise HTTPException(status_code=400, detail="No se puede cancelar una cita completada")

    # Ejecutar actualizacion
    cita_actualizada = await cita_service.actualizar_estado(session, cita_id, data)

    logger.info(
        "[CITAS] %s #%s actualizo cita #%s a '%s'",
        rol, user["id"], cita_id, data.estado
    )
    return cita_actualizada


# =============================================================================
# Eliminar cita (solo admin)
# =============================================================================
@router.delete("/{cita_id}")
async def eliminar_cita(
    cita_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(require_role("admin")),
):
    """Eliminar una cita permanentemente. Solo admin."""
    cita = await session.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    await session.delete(cita)
    await session.flush()

    logger.info("[CITAS] Admin elimino cita #%s", cita_id)
    return {"mensaje": "Cita eliminada permanentemente", "cita_id": cita_id}
