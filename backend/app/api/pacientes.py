from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import SessionLocal, get_db
from app.models import schemas, crud

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

@router.post("/", response_model=schemas.PacienteResponse, status_code=201)
def crear_paciente(paciente: schemas.PacienteCreate, db: Session = Depends(get_db)):
    existente = crud.get_paciente_by_documento(db, paciente.documento)
    if existente:
        raise HTTPException(status_code=400, detail="Documento ya registrado")
    return crud.create_paciente(db, paciente)

@router.get("/", response_model=List[schemas.PacienteResponse])
def listar_pacientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(crud.database.Paciente).offset(skip).limit(limit).all()

@router.get("/{paciente_id}", response_model=schemas.PacienteResponse)
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = crud.get_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente