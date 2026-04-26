"""Esquemas Pydantic para validación de entrada/salida."""
from datetime import date, time, datetime
from pydantic import BaseModel, EmailStr, Field


# ── Pacientes ──

class PacienteCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    documento: str = Field(..., min_length=5, max_length=50)
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=30)
    fecha_nacimiento: date


class PacienteResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    documento: str
    email: str
    telefono: str
    fecha_nacimiento: date
    creado_en: datetime

    model_config = {"from_attributes": True}


# ── Doctores ──

class DoctorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    especialidad: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=30)


class DoctorResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    especialidad: str
    email: str
    telefono: str
    activo: bool
    creado_en: datetime

    model_config = {"from_attributes": True}


# ── Horarios ──

class HorarioCreate(BaseModel):
    doctor_id: int
    dia_semana: int = Field(..., ge=0, le=6)
    hora_inicio: time
    hora_fin: time


class HorarioResponse(BaseModel):
    id: int
    doctor_id: int
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    activo: bool

    model_config = {"from_attributes": True}


# ── Citas ──

class CitaCreate(BaseModel):
    paciente_id: int
    doctor_id: int
    fecha: date
    hora: time
    motivo: str = Field(..., min_length=5, max_length=300)


class CitaUpdateEstado(BaseModel):
    estado: str = Field(..., pattern="^(pendiente|confirmada|cancelada|completada)$")
    notas: str | None = None


class CitaResponse(BaseModel):
    id: int
    paciente_id: int
    doctor_id: int
    fecha: date
    hora: time
    estado: str
    motivo: str
    notas: str | None
    creado_en: datetime

    model_config = {"from_attributes": True}


class CitaDetalle(CitaResponse):
    """Respuesta expandida con datos del paciente y doctor."""
    paciente_nombre: str
    paciente_apellido: str
    doctor_nombre: str
    doctor_apellido: str
    doctor_especialidad: str

    model_config = {"from_attributes": True}