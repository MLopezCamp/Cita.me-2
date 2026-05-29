"""
cita.me — Utilidades de seguridad: hashing y JWT
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from config_auth import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES


# =============================================================================
# Schemas para token
# =============================================================================
class TokenPayload(BaseModel):
    sub: str      # formato: "{rol}:{id}"  ej: "doctor:5"
    rol: str
    exp: datetime | None = None


# =============================================================================
# Funciones de password
# =============================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# =============================================================================
# Funciones de JWT
# =============================================================================
def create_access_token(
    rol: str,
    user_id: int,
    expires_delta: timedelta | None = None
) -> str:
    """
    Genera un JWT firmado con el rol y ID del usuario.
    
    Args:
        rol: El rol del usuario (admin, doctor, paciente, administrativo)
        user_id: El ID numerico del usuario en su tabla
        expires_delta: Tiempo de expiracion custom. Por defecto 8 horas.
    
    Returns:
        El token JWT codificado como string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": f"{rol}:{user_id}",
        "rol": rol,
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenPayload | None:
    """
    Decodifica y valida un JWT.
    
    Args:
        token: El token JWT a validar.
    
    Returns:
        TokenPayload con los datos del token, o None si es invalido/expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        rol: str = payload.get("rol")
        if sub is None or rol is None:
            return None
        return TokenPayload(sub=sub, rol=rol)
    except JWTError:
        return None
