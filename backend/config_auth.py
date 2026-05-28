"""
cita.me — Configuracion de autenticacion JWT
"""
import os

# =============================================================================
# JWT Settings
# =============================================================================
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "cita-me-dev-secret-key-change-in-production-2025"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas

# =============================================================================
# Roles validos del sistema
# =============================================================================
ROLES = ["admin", "doctor", "paciente", "administrativo"]

# =============================================================================
# Permisos por rol
# Formato: "recurso:accion"
# =============================================================================
PERMISOS = {
    "admin": [
        # Citas — CRUD completo
        "citas:crear", "citas:leer", "citas:actualizar", "citas:borrar",
        "citas:confirmar", "citas:cancelar", "citas:completar",
        # Doctores — CRUD completo
        "doctores:crear", "doctores:leer", "doctores:actualizar", "doctores:borrar",
        # Pacientes — CRUD completo
        "pacientes:crear", "pacientes:leer", "pacientes:actualizar", "pacientes:borrar",
        # Horarios — CRUD completo
        "horarios:crear", "horarios:leer", "horarios:actualizar", "horarios:borrar",
        # Administrativos — CRUD completo
        "administrativos:crear", "administrativos:leer",
        "administrativos:actualizar", "administrativos:borrar",
        # Partes medicos
        "partes_medicos:crear", "partes_medicos:leer",
    ],
    "doctor": [
        # Citas — solo las suyas
        "citas:leer", "citas:confirmar", "citas:completar", "citas:cancelar",
        # Partes medicos — solo los suyos
        "partes_medicos:crear", "partes_medicos:leer",
    ],
    "paciente": [
        # Citas — solo las propias
        "citas:crear", "citas:leer", "citas:cancelar",
    ],
    "administrativo": [
        # Citas — gestion completa (no completar)
        "citas:crear", "citas:leer", "citas:confirmar", "citas:cancelar",
        # Horarios — gestion completa
        "horarios:crear", "horarios:leer", "horarios:actualizar",
        # No puede: completar citas, crear doctores/pacientes, crear administrativos
    ],
}


def tiene_permiso(rol: str, permiso: str) -> bool:
    """Verifica si un rol tiene un permiso especifico."""
    return permiso in PERMISOS.get(rol, [])
