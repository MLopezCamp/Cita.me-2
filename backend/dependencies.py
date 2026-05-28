"""
cita.me — Dependencias de autenticacion para FastAPI

Estas funciones se inyectan en los routers usando Depends() para proteger
los endpoints segun el rol y los permisos del usuario autenticado.

Uso tipico:
    @router.get("/")
    async def listar(user: dict = Depends(get_current_user)):
        ...

    @router.post("/")
    async def crear(user: dict = Depends(require_role("admin"))):
        ...

    @router.put("/confirmar")
    async def confirmar(user: dict = Depends(require_any_role("admin", "administrativo"))):
        ...
"""
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config_auth import PERMISOS
from database import get_session
from models import Paciente, Doctor, Administrativo
from security import decode_access_token

logger = logging.getLogger(__name__)

# =============================================================================
# Esquema de seguridad HTTP Bearer
# =============================================================================
security_scheme = HTTPBearer(auto_error=False)


# =============================================================================
# Dependencia base: extraer usuario del token JWT
# =============================================================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_session)
) -> dict:
    """
    Extrae y valida el usuario desde el token JWT en el header Authorization.
    
    Returns:
        dict con: {id, rol, obj}
        - id: int, el ID del usuario
        - rol: str, el rol del usuario
        - obj: el objeto ORM del usuario (Paciente, Doctor, Administrativo, o dict para admin)
    
    Raises:
        HTTPException 401 si no hay token, es invalido, o el usuario no existe.
    """
    # --- Verificar que existe el token ---
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Decodificar el token ---
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Parsear "sub" = "rol:id" ---
    try:
        rol, user_id_str = token_data.sub.split(":")
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado",
        )

    # --- Cargar el usuario segun su rol ---
    usuario = None

    if rol == "admin":
        # El admin es un usuario especial (id=0, no esta en BD)
        usuario = {
            "id": 0,
            "nombre": "Administrador",
            "rol": "admin"
        }

    elif rol == "paciente":
        stmt = select(Paciente).where(Paciente.id == user_id)
        result = await session.execute(stmt)
        usuario = result.scalar_one_or_none()

    elif rol == "doctor":
        stmt = select(Doctor).where(
            Doctor.id == user_id,
            Doctor.activo == True
        )
        result = await session.execute(stmt)
        usuario = result.scalar_one_or_none()

    elif rol == "administrativo":
        stmt = select(Administrativo).where(
            Administrativo.id == user_id,
            Administrativo.activo == True
        )
        result = await session.execute(stmt)
        usuario = result.scalar_one_or_none()

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Rol no valido: {rol}",
        )

    # --- Verificar que el usuario existe ---
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    return {"id": user_id, "rol": rol, "obj": usuario}


# =============================================================================
# Dependencia: exigir un rol especifico
# =============================================================================
def require_role(required_rol: str):
    """
    Crea una dependencia que exige un rol especifico.
    
    Uso:
        @router.get("/admin-only")
        async def endpoint(user: dict = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user["rol"] != required_rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol '{required_rol}'",
            )
        return user
    return role_checker


# =============================================================================
# Dependencia: aceptar multiples roles
# =============================================================================
def require_any_role(*roles: str):
    """
    Crea una dependencia que acepta cualquiera de los roles indicados.
    
    Uso:
        @router.post("/citas")
        async def crear_cita(user: dict = Depends(require_any_role("admin", "administrativo"))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user["rol"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {list(roles)}",
            )
        return user
    return role_checker


# =============================================================================
# Dependencia: verificar permiso especifico
# =============================================================================
def require_permiso(permiso: str):
    """
    Crea una dependencia que verifica un permiso especifico.
    
    Uso:
        @router.post("/citas")
        async def crear(user: dict = Depends(require_permiso("citas:crear"))):
            ...
    """
    async def permiso_checker(user: dict = Depends(get_current_user)) -> dict:
        rol = user["rol"]
        if permiso not in PERMISOS.get(rol, []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado: '{permiso}'",
            )
        return user
    return require_permiso
