"""Configuración del visor de base de datos."""
import os

# Ruta al archivo SQLite — mismo volumen que el backend
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/data/citame.db"
)

DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"