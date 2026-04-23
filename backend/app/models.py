from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from .database import Base
import enum

class CitaEstado(str, enum.Enum):
    AGENDADA = "agendada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"

class Paciente(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), nullable=False)

class Medico(Base):
    __tablename__ = "medicos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    especialidad = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)

class Horario(Base):
    __tablename__ = "horarios"
    id = Column(Integer, primary_key=True, index=True)
    medico_id = Column(Integer, nullable=False)
    dia_semana = Column(String(20), nullable=False)
    hora_inicio = Column(String(5), nullable=False)
    hora_fin = Column(String(5), nullable=False)

class Cita(Base):
    __tablename__ = "citas"
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, nullable=False)
    medico_id = Column(Integer, nullable=False)
    fecha = Column(String(10), nullable=False)   # YYYY-MM-DD
    hora = Column(String(5), nullable=False)     # HH:MM
    motivo = Column(Text, nullable=True)
    estado = Column(Enum(CitaEstado), default=CitaEstado.AGENDADA)