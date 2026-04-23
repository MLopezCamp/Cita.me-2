from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from .database import get_db, engine, Base
from .models import Paciente, Medico, Horario, Cita, CitaEstado
from .tasks import enviar_correo_confirmacion
from .redis_lock import redis_lock
from .config import config

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Citas Medicas Distribuido")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelos Pydantic ---
class PacienteCreate(BaseModel):
    nombre: str
    documento: str
    email: str

class PacienteResponse(PacienteCreate):
    id: int

class MedicoCreate(BaseModel):
    nombre: str
    especialidad: str
    email: str

class MedicoResponse(MedicoCreate):
    id: int

class HorarioCreate(BaseModel):
    medico_id: int
    dia_semana: str
    hora_inicio: str
    hora_fin: str

class HorarioResponse(HorarioCreate):
    id: int

class CitaCreate(BaseModel):
    paciente_id: int
    medico_id: int
    fecha: str
    hora: str
    motivo: Optional[str] = None

class CitaResponse(CitaCreate):
    id: int
    estado: str

# --- Endpoints Pacientes ---
@app.post("/pacientes", response_model=PacienteResponse, status_code=201)
def crear_paciente(paciente: PacienteCreate, db: Session = Depends(get_db)):
    db_paciente = Paciente(**paciente.dict())
    db.add(db_paciente)
    db.commit()
    db.refresh(db_paciente)
    return db_paciente

@app.get("/pacientes", response_model=List[PacienteResponse])
def listar_pacientes(db: Session = Depends(get_db)):
    return db.query(Paciente).all()

# --- Endpoints Medicos ---
@app.post("/medicos", response_model=MedicoResponse, status_code=201)
def crear_medico(medico: MedicoCreate, db: Session = Depends(get_db)):
    db_medico = Medico(**medico.dict())
    db.add(db_medico)
    db.commit()
    db.refresh(db_medico)
    return db_medico

@app.get("/medicos", response_model=List[MedicoResponse])
def listar_medicos(db: Session = Depends(get_db)):
    return db.query(Medico).all()

@app.get("/medicos/{medico_id}", response_model=MedicoResponse)
def obtener_medico(medico_id: int, db: Session = Depends(get_db)):
    medico = db.query(Medico).filter(Medico.id == medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Medico no encontrado")
    return medico

# --- Endpoints Horarios ---
@app.post("/horarios", response_model=HorarioResponse, status_code=201)
def crear_horario(horario: HorarioCreate, db: Session = Depends(get_db)):
    db_horario = Horario(**horario.dict())
    db.add(db_horario)
    db.commit()
    db.refresh(db_horario)
    return db_horario

@app.get("/horarios/medico/{medico_id}", response_model=List[HorarioResponse])
def listar_horarios_medico(medico_id: int, db: Session = Depends(get_db)):
    return db.query(Horario).filter(Horario.medico_id == medico_id).all()

# --- Endpoints Citas con locking distribuido y tarea asincrona ---
@app.post("/citas", response_model=CitaResponse, status_code=201)
async def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    # Verificar que paciente y medico existen
    paciente = db.query(Paciente).filter(Paciente.id == cita.paciente_id).first()
    medico = db.query(Medico).filter(Medico.id == cita.medico_id).first()
    if not paciente or not medico:
        raise HTTPException(status_code=404, detail="Paciente o medico no encontrado")
    
    lock_key = f"lock:cita:{cita.medico_id}:{cita.fecha}:{cita.hora}"
    
    async with redis_lock(lock_key) as acquired:
        if not acquired:
            raise HTTPException(status_code=409, detail="El horario esta siendo reservado por otro usuario")
        
        # Verificar si ya existe una cita en ese mismo horario
        existing = db.query(Cita).filter(
            Cita.medico_id == cita.medico_id,
            Cita.fecha == cita.fecha,
            Cita.hora == cita.hora,
            Cita.estado == CitaEstado.AGENDADA
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="El medico ya tiene una cita en ese horario")
        
        # Crear cita
        db_cita = Cita(**cita.dict(), estado=CitaEstado.AGENDADA)
        db.add(db_cita)
        db.commit()
        db.refresh(db_cita)
    
    # Encolar tarea asincrona para enviar correo
    enviar_correo_confirmacion.delay(
        cita_id=db_cita.id,
        email_paciente=paciente.email,
        medico_nombre=medico.nombre,
        fecha=cita.fecha,
        hora=cita.hora
    )
    
    return db_cita

@app.get("/citas", response_model=List[CitaResponse])
def listar_citas(db: Session = Depends(get_db)):
    return db.query(Cita).all()

@app.get("/citas/{cita_id}", response_model=CitaResponse)
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@app.put("/citas/{cita_id}/cancelar")
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if cita.estado != CitaEstado.AGENDADA:
        raise HTTPException(status_code=400, detail="La cita no se puede cancelar")
    cita.estado = CitaEstado.CANCELADA
    db.commit()
    return {"message": "Cita cancelada exitosamente"}