"""
cita.me — Punto de entrada FastAPI
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from redis_client import init_redis, close_redis
from messaging.producer import close_producer
from logging_config import setup_logging
from middleware.request_id import RequestIdMiddleware

# Routers
from routers import (
    pacientes,
    doctores,
    horarios,
    citas,
    auth,
    portal,
    doctor_portal,
    administrativos,    
    partes_medicos,     
)

setup_logging()
logger = logging.getLogger("cita.me")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[INIT] Iniciando cita.me")
    await init_db()
    await init_redis()
    logger.info("[INIT] cita.me listo")
    yield
    logger.info("[SHUTDOWN] Apagando cita.me")
    await close_producer()
    await close_redis()
    logger.info("[SHUTDOWN] Conexiones cerradas")


app = FastAPI(
    title="cita.me",
    description="Sistema de reservas de citas medicas con autenticacion JWT",
    version="2.0.0",
    lifespan=lifespan,
)

# =============================================================================
# Middleware
# =============================================================================
app.add_middleware(RequestIdMiddleware)

_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Routers
# =============================================================================
app.include_router(auth.router)
app.include_router(pacientes.router)
app.include_router(doctores.router)
app.include_router(horarios.router)
app.include_router(citas.router)
app.include_router(portal.router)
app.include_router(doctor_portal.router)
app.include_router(administrativos.router)    
app.include_router(partes_medicos.router)     


# =============================================================================
# Health Check
# =============================================================================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cita.me", "version": "2.0.0"}


@app.get("/")
async def root():
    return {"app": "cita.me", "version": "2.0.0", "docs": "/docs"}
