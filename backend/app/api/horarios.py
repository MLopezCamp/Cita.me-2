from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import SessionLocal, get_db
from app.models import schemas, crud
from app.api.auth import verify_token

router = APIRouter(prefix="/horarios", tags=["horarios"])

@router.post("/", response_model=schemas.HorarioResponse, status_code=201)
def crear_horario(horario: schemas.HorarioCreate, db: Session = Depends(get_db), _=Depends(verify_token)):
    medico = crud.get_medico(db, horario.medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return crud.create_horario(db, horario)

@router.get("/medico/{medico_id}", response_model=List[schemas.HorarioResponse])
def listar_horarios_medico(medico_id: int, db: Session = Depends(get_db)):
    return crud.get_horarios_by_medico(db, medico_id)

@router.delete("/{horario_id}")
def eliminar_horario(horario_id: int, db: Session = Depends(get_db), _=Depends(verify_token)):
    deleted = crud.delete_horario(db, horario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    return {"detail": "Horario eliminado"}