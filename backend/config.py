"""Configuración centralizada de cita.me"""
import os
from dotenv import load_dotenv

load_dotenv()

# Apunta al mismo volumen compartido
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////data/citame.db")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@localhost:5672/"
)

LOCK_TIMEOUT_SECONDS = int(os.getenv("LOCK_TIMEOUT", "15"))
LOCK_WAIT_SECONDS = int(os.getenv("LOCK_WAIT", "10"))

QUEUE_CITAS = "citame.eventos"
EXCHANGE_CITAS = "citame.exchange"

CACHE_TTL = 300