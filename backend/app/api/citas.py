from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.database import SessionLocal, get_db
from app.models import schemas, crud
from app.services.locking import distributed_lock
from app.tasks.tasks import enviar_confirmacion_cita

router = APIRouter(prefix="/citas", tags=["citas"])

@router.post("/", response_model=schemas.CitaResponse, status_code=201)
async def crear_cita(
    cita: schemas.CitaCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    paciente = crud.get_paciente(db, cita.paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    medico = crud.get_medico(db, cita.medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    lock_key = f"lock:cita:{cita.medico_id}:{cita.fecha.isoformat()}"
    async with distributed_lock(lock_key, expire_time=10) as acquired:
        if not acquired:
            raise HTTPException(status_code=409, detail="Horario en proceso de reserva")
        nueva_cita = crud.create_cita(db, cita)
        background_tasks.add_task(
            enviar_confirmacion_cita.delay,
            nueva_cita.id,
            paciente.email,
            paciente.nombre,
            nueva_cita.fecha.isoformat()
        )
        return nueva_cita

@router.get("/", response_model=List[schemas.CitaResponse])
def listar_citas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(crud.database.Cita).offset(skip).limit(limit).all()

@router.get("/{cita_id}", response_model=schemas.CitaResponse)
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = crud.get_cita(db, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.put("/{cita_id}/cancelar", response_model=schemas.CitaResponse)
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = crud.cancelar_cita(db, cita_id)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.get("/paciente/{paciente_id}", response_model=List[schemas.CitaResponse])
def citas_por_paciente(paciente_id: int, db: Session = Depends(get_db)):
    return crud.get_citas_by_paciente(db, paciente_id)

@router.get("/medico/{medico_id}", response_model=List[schemas.CitaResponse])
def citas_por_medico(medico_id: int, db: Session = Depends(get_db)):
    return crud.get_citas_by_medico(db, medico_id)