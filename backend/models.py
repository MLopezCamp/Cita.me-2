"""Modelos ORM — definicion de tablas."""
from datetime import date, time, datetime
from sqlalchemy import String, Integer, ForeignKey, Date, Time, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


# =============================================================================
# PACIENTE
# =============================================================================
class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    documento: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    # NUEVO: Hash de contrasena para autenticacion JWT
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="$2b$12$dummyhashforseededpatients"
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacion: un paciente tiene muchas citas
    citas: Mapped[list["Cita"]] = relationship(
        back_populates="paciente",
        cascade="all, delete-orphan"
    )


# =============================================================================
# DOCTOR
# =============================================================================
class Doctor(Base):
    __tablename__ = "doctores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    especialidad: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    # NUEVO: Hash de contrasena para autenticacion JWT
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="$2b$12$dummyhashforseededdoctors"
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    horarios: Mapped[list["Horario"]] = relationship(
        back_populates="doctor",
        cascade="all, delete-orphan"
    )
    citas: Mapped[list["Cita"]] = relationship(
        back_populates="doctor",
        cascade="all, delete-orphan"
    )


# =============================================================================
# ADMINISTRATIVO (NUEVO)
# =============================================================================
class Administrativo(Base):
    __tablename__ = "administrativos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# HORARIO
# =============================================================================
class Horario(Base):
    __tablename__ = "horarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctores.id"), nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=lunes, 6=domingo
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    doctor: Mapped["Doctor"] = relationship(back_populates="horarios")


# =============================================================================
# CITA
# =============================================================================
class Cita(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    paciente_id: Mapped[int] = mapped_column(Integer, ForeignKey("pacientes.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctores.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")  # pendiente|confirmada|cancelada|completada
    motivo: Mapped[str] = mapped_column(String(300), nullable=False)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    paciente: Mapped["Paciente"] = relationship(back_populates="citas")
    doctor: Mapped["Doctor"] = relationship(back_populates="citas")
    # NUEVO: Relacion con parte medico (una cita puede tener cero o un parte medico)
    parte_medico: Mapped["ParteMedico" | None] = relationship(
        back_populates="cita",
        uselist=False,
        cascade="all, delete-orphan"
    )


# =============================================================================
# PARTE MEDICO (NUEVO)
# =============================================================================
class ParteMedico(Base):
    __tablename__ = "partes_medicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cita_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("citas.id"),
        nullable=False,
        unique=True
    )
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctores.id"), nullable=False)
    diagnostico: Mapped[str] = mapped_column(Text, nullable=False)
    tratamiento: Mapped[str | None] = mapped_column(Text, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacion: un parte medico pertenece a una cita
    cita: Mapped["Cita"] = relationship(back_populates="parte_medico")
