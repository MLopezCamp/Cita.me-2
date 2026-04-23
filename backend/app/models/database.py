from sqlalchemy import create_engine, Column, Integer, String, DateTime, Time, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EstadoCita(str, enum.Enum):
    agendada = "agendada"
    cancelada = "cancelada"
    completada = "completada"

class Paciente(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(20))
    citas = relationship("Cita", back_populates="paciente")

class Medico(Base):
    __tablename__ = "medicos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    especialidad = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(20))
    horarios = relationship("Horario", back_populates="medico")
    citas = relationship("Cita", back_populates="medico")

class Horario(Base):
    __tablename__ = "horarios"
    id = Column(Integer, primary_key=True, index=True)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    dia_semana = Column(String(20), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    medico = relationship("Medico", back_populates="horarios")

class Cita(Base):
    __tablename__ = "citas"
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    motivo = Column(Text)
    estado = Column(Enum(EstadoCita), default=EstadoCita.agendada)
    created_at = Column(DateTime, default=datetime.utcnow)
    paciente = relationship("Paciente", back_populates="citas")
    medico = relationship("Medico", back_populates="citas")

class Administrador(Base):
    __tablename__ = "administradores"
    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)