from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import SessionLocal, get_db
from app.models import schemas, crud
from app.api.auth import verify_token

router = APIRouter(prefix="/medicos", tags=["medicos"])

@router.post("/", response_model=schemas.MedicoResponse, status_code=201)
def crear_medico(medico: schemas.MedicoCreate, db: Session = Depends(get_db), _=Depends(verify_token)):
    return crud.create_medico(db, medico)

@router.get("/", response_model=List[schemas.MedicoResponse])
def listar_medicos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_medicos(db, skip, limit)

@router.get("/{medico_id}", response_model=schemas.MedicoResponse)
def obtener_medico(medico_id: int, db: Session = Depends(get_db)):
    medico = crud.get_medico(db, medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return medico

@router.put("/{medico_id}", response_model=schemas.MedicoResponse)
def actualizar_medico(medico_id: int, medico: schemas.MedicoCreate, db: Session = Depends(get_db), _=Depends(verify_token)):
    updated = crud.update_medico(db, medico_id, medico)
    if not updated:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return updated

@router.delete("/{medico_id}")
def eliminar_medico(medico_id: int, db: Session = Depends(get_db), _=Depends(verify_token)):
    deleted = crud.delete_medico(db, medico_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return {"detail": "Médico eliminado"}