"""
cita.me — Autenticacion JWT (Admin, Doctor, Paciente, Administrativo)
Login unificado que devuelve un token JWT para todos los roles.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependencies import get_current_user
from models import Paciente, Doctor, Administrativo
from schemas import LoginRequest, LoginResponse
from security import verify_password, create_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticacion"])


# =============================================================================
# LOGIN — Unificado para los 4 roles
# =============================================================================
@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Login unificado para los cuatro roles del sistema.

    **Roles y identifiers:**
    - `admin` — identifier: "admin", contrasena: "admin"
    - `doctor` — identifier: email del doctor, contrasena: "1234" (o la registrada)
    - `paciente` — identifier: numero de documento, contrasena: "1234" (o la registrada)
    - `administrativo` — identifier: email del administrativo, contrasena: "1234" (o la registrada)
    """
    user_id = None
    nombre = None
    especialidad = None
    documento = None

    # ── ADMIN ──
    if data.rol == "admin":
        if data.identifier != "admin" or data.contrasena != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de administrador incorrectas"
            )
        user_id = 0
        nombre = "Administrador"

    # ── DOCTOR ──
    elif data.rol == "doctor":
        stmt = select(Doctor).where(
            Doctor.email == data.identifier,
            Doctor.activo == True
        )
        result = await session.execute(stmt)
        doctor = result.scalar_one_or_none()

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Doctor no encontrado con ese email"
            )

        # TODO: En produccion, usar verify_password(data.contrasena, doctor.password_hash)
        # Por ahora, mantenemos compatibilidad con datos existentes
        if data.contrasena != "1234":
            # Intentar con hash bcrypt si ya migro
            from security import verify_password as vp
            if not vp(data.contrasena, doctor.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Contrasena incorrecta"
                )

        user_id = doctor.id
        nombre = f"Dr. {doctor.nombre} {doctor.apellido}"
        especialidad = doctor.especialidad

    # ── PACIENTE ──
    elif data.rol == "paciente":
        stmt = select(Paciente).where(Paciente.documento == data.identifier)
        result = await session.execute(stmt)
        paciente = result.scalar_one_or_none()

        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Paciente no encontrado con ese documento"
            )

        if data.contrasena != "1234":
            from security import verify_password as vp
            if not vp(data.contrasena, paciente.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Contrasena incorrecta"
                )

        user_id = paciente.id
        nombre = f"{paciente.nombre} {paciente.apellido}"
        documento = paciente.documento

    # ── ADMINISTRATIVO ──
    elif data.rol == "administrativo":
        stmt = select(Administrativo).where(
            Administrativo.email == data.identifier,
            Administrativo.activo == True
        )
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Administrativo no encontrado con ese email"
            )

        if data.contrasena != "1234":
            from security import verify_password as vp
            if not vp(data.contrasena, admin.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Contrasena incorrecta"
                )

        user_id = admin.id
        nombre = f"{admin.nombre} {admin.apellido}"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol no valido. Use: admin, doctor, paciente, administrativo"
        )

    # Generar token JWT
    token = create_access_token(data.rol, user_id)

    logger.info("[AUTH] Login exitoso: %s (ID:%s)", data.rol, user_id)

    return LoginResponse(
        access_token=token,
        id=user_id,
        nombre=nombre,
        rol=data.rol,
        especialidad=especialidad,
        documento=documento,
    )


# =============================================================================
# ME — Obtener datos del usuario autenticado
# =============================================================================
@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """Retorna la informacion basica del usuario autenticado."""
    return {
        "id": user["id"],
        "rol": user["rol"],
    }


# =============================================================================
# LISTA DE DOCTORES (para formulario de login)
# =============================================================================
@router.get("/doctores-lista")
async def lista_doctores_emails(
    session: AsyncSession = Depends(get_session)
):
    """Lista de emails de doctores activos para el formulario de login."""
    stmt = select(
        Doctor.id, Doctor.email, Doctor.nombre,
        Doctor.apellido, Doctor.especialidad
    ).where(Doctor.activo == True)

    result = await session.execute(stmt)
    return [
        {
            "id": r[0],
            "email": r[1],
            "nombre": f"Dr. {r[2]} {r[3]}",
            "especialidad": r[4]
        }
        for r in result.all()
    ]


# =============================================================================
# LISTA DE ADMINISTRATIVOS (para formulario de login)
# =============================================================================
@router.get("/administrativos-lista")
async def lista_administrativos_emails(
    session: AsyncSession = Depends(get_session)
):
    """Lista de emails de administrativos activos para el formulario de login."""
    stmt = select(
        Administrativo.id, Administrativo.email,
        Administrativo.nombre, Administrativo.apellido
    ).where(Administrativo.activo == True)

    result = await session.execute(stmt)
    return [
        {
            "id": r[0],
            "email": r[1],
            "nombre": f"{r[2]} {r[3]}"
        }
        for r in result.all()
    ]
