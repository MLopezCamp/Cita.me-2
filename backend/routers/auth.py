"""
cita.me — Autenticación general (Admin, Doctor, Paciente)
Credenciales fijas para proyecto universitario:
  Admin: usuario=admin, contraseña=admin
  Doctor: email + contraseña=1234
  Paciente: documento + contraseña=1234
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import get_session
from models import Paciente, Doctor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])


class LoginRequest(BaseModel):
    rol: str  # "admin", "doctor", "paciente"
    usuario: Optional[str] = None
    email: Optional[str] = None
    documento: Optional[str] = None
    contrasena: Optional[str] = None


class LoginResponse(BaseModel):
    id: int
    nombre: str
    rol: str
    especialidad: Optional[str] = None
    documento: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    """Login unificado para los tres roles."""

    # ── Admin ──
    if data.rol == "admin":
        if data.usuario != "admin" or data.contrasena != "admin":
            raise HTTPException(status_code=401, detail="Credenciales de admin incorrectas")
        logger.info("[cita.me/AUTH] Admin login exitoso")
        return LoginResponse(id=0, nombre="Administrador", rol="admin")

    # ── Doctor ──
    elif data.rol == "doctor":
        if data.contrasena != "1234":
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        if not data.email:
            raise HTTPException(status_code=400, detail="Email requerido para doctor")
        stmt = select(Doctor).where(Doctor.email == data.email, Doctor.activo == True)
        resultado = await session.execute(stmt)
        doctor = resultado.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=401, detail="Doctor no encontrado con ese email")
        logger.info("[cita.me/AUTH] Doctor login: %s %s (ID:%s)", doctor.nombre, doctor.apellido, doctor.id)
        return LoginResponse(
            id=doctor.id,
            nombre=f"Dr. {doctor.nombre} {doctor.apellido}",
            rol="doctor",
            especialidad=doctor.especialidad,
        )

    # ── Paciente ──
    elif data.rol == "paciente":
        if data.contrasena != "1234":
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        if not data.documento:
            raise HTTPException(status_code=400, detail="Documento requerido para paciente")
        stmt = select(Paciente).where(Paciente.documento == data.documento)
        resultado = await session.execute(stmt)
        paciente = resultado.scalar_one_or_none()
        if not paciente:
            raise HTTPException(status_code=401, detail="Paciente no encontrado con ese documento")
        logger.info("[cita.me/AUTH] Paciente login: %s %s (ID:%s)", paciente.nombre, paciente.apellido, paciente.id)
        return LoginResponse(
            id=paciente.id,
            nombre=f"{paciente.nombre} {paciente.apellido}",
            rol="paciente",
            documento=paciente.documento,
        )

    else:
        raise HTTPException(status_code=400, detail="Rol no válido. Use: admin, doctor, paciente")


@router.get("/doctores-lista")
async def lista_doctores_emails(session: AsyncSession = Depends(get_session)):
    """Lista de emails de doctores para el formulario de login."""
    stmt = select(Doctor.id, Doctor.email, Doctor.nombre, Doctor.apellido, Doctor.especialidad).where(Doctor.activo == True)
    resultado = await session.execute(stmt)
    return [
        {"id": r[0], "email": r[1], "nombre": f"Dr. {r[2]} {r[3]}", "especialidad": r[4]}
        for r in resultado.all()
    ]