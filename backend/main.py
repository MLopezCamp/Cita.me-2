"""
cita.me — Punto de entrada FastAPI.

Ciclo de vida:
- Startup: init DB, Redis, heartbeat de coordinacion, consumers RabbitMQ
- Shutdown: cancelar tareas, cerrar conexiones
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from redis_client import init_redis, close_redis, check_service_health
from messaging.producer import close_producer
from messaging.consumer import start_all_consumers

from routers import pacientes, doctores, horarios, citas, auth, portal, doctor_portal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

consumer_task: asyncio.Task | None = None
heartbeat_task: asyncio.Task | None = None


async def _heartbeat_loop():
    """
    Registrar heartbeat de servicios en Redis cada 5 segundos.
    Permite saber que servicios estan activos (coordinacion).
    Los heartbeats tienen TTL de 10s: si un servicio cae, desaparece automaticamente.
    """
    while True:
        try:
            await check_service_health("backend-api")
            await check_service_health("consumer-rabbitmq")
        except Exception:
            pass
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicacion."""
    global consumer_task, heartbeat_task

    logger.info("=== cita.me — INICIANDO ===")

    # Base de datos
    await init_db()

    # Redis
    await init_redis()

    # Heartbeat de coordinacion: registra servicios activos en Redis
    heartbeat_task = asyncio.create_task(_heartbeat_loop())

    # Consumers RabbitMQ: tres servicios desacoplados en background
    consumer_task = asyncio.create_task(start_all_consumers())
    logger.info("[cita.me] Servicios desacoplados + heartbeat iniciados")

    logger.info("=== cita.me — LISTO ===")

    yield

    logger.info("=== cita.me — APAGANDO ===")

    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    await close_producer()
    await close_redis()
    logger.info("=== cita.me — CONEXIONES CERRADAS ===")


app = FastAPI(
    title="cita.me",
    description="Sistema de reservas de citas médicas",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pacientes.router)
app.include_router(doctores.router)
app.include_router(horarios.router)
app.include_router(citas.router)
app.include_router(portal.router)
app.include_router(doctor_portal.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cita.me"}


@app.get("/")
async def root():
    return {"app": "cita.me", "docs": "/docs"}