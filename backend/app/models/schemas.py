from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, time
from typing import Optional
from enum import Enum

class EstadoCitaEnum(str, Enum):
    agendada = "agendada"
    cancelada = "cancelada"
    completada = "completada"

class PacienteCreate(BaseModel):
    nombre: str
    documento: str
    email: EmailStr
    telefono: Optional[str] = None

class PacienteResponse(PacienteCreate):
    id: int

class MedicoCreate(BaseModel):
    nombre: str
    especialidad: str
    email: EmailStr
    telefono: Optional[str] = None

class MedicoResponse(MedicoCreate):
    id: int

class HorarioCreate(BaseModel):
    medico_id: int
    dia_semana: str
    hora_inicio: time
    hora_fin: time

class HorarioResponse(HorarioCreate):
    id: int

class CitaCreate(BaseModel):
    paciente_id: int
    medico_id: int
    fecha: datetime
    motivo: str

class CitaResponse(BaseModel):
    id: int
    paciente_id: int
    medico_id: int
    fecha: datetime
    motivo: str
    estado: EstadoCitaEnum
    created_at: datetime

class LoginRequest(BaseModel):
    usuario: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"