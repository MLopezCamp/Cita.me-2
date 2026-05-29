"""Esquemas Pydantic para validacion de entrada/salida."""
from datetime import date, time, datetime
from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# AUTH / JWT
# =============================================================================

class LoginRequest(BaseModel):
    rol: str  # "admin", "doctor", "paciente", "administrativo"
    identifier: str  # email para doctor/administrativo, documento para paciente, "admin" para admin
    contrasena: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    id: int
    nombre: str
    rol: str
    especialidad: str | None = None
    documento: str | None = None


# =============================================================================
# ADMINISTRATIVO
# =============================================================================

class AdministrativoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=30)
    contrasena: str = Field(..., min_length=4)


class AdministrativoResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    telefono: str
    activo: bool
    creado_en: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# PARTE MEDICO
# =============================================================================

class ParteMedicoCreate(BaseModel):
    cita_id: int
    diagnostico: str = Field(..., min_length=5)
    tratamiento: str | None = None
    observaciones: str | None = None


class ParteMedicoResponse(BaseModel):
    id: int
    cita_id: int
    doctor_id: int
    diagnostico: str
    tratamiento: str | None
    observaciones: str | None
    creado_en: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# PACIENTES
# =============================================================================

class PacienteCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    documento: str = Field(..., min_length=5, max_length=50)
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=30)
    fecha_nacimiento: date
    contrasena: str | None = Field(default="1234", min_length=4)


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


# =============================================================================
# DOCTORES
# =============================================================================

class DoctorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    especialidad: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    telefono: str = Field(..., min_length=7, max_length=30)
    contrasena: str | None = Field(default="1234", min_length=4)


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


# =============================================================================
# HORARIOS
# =============================================================================

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


# =============================================================================
# CITAS
# =============================================================================

class CitaCreate(BaseModel):
    paciente_id: int
    doctor_id: int
    fecha: date
    hora: time
    motivo: str = Field(..., min_length=5, max_length=300)


class CitaCreatePortal(BaseModel):
    """Schema para el portal del paciente — paciente_id lo inyecta el JWT."""
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
