"""
cita.me — Punto de entrada FastAPI
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from redis_client import init_redis, close_redis
from messaging.producer import close_producer
from messaging.consumer import start_consumer

from routers import pacientes, doctores, horarios, citas, auth, portal, doctor_portal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    logger.info("=== cita.me — INICIANDO ===")
    await init_db()
    await init_redis()
    consumer_task = asyncio.create_task(start_consumer())
    logger.info("[cita.me] Consumer RabbitMQ en background")
    logger.info("=== cita.me — LISTO ===")
    yield
    logger.info("=== cita.me — APAGANDO ===")
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