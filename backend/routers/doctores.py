from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_session
from ..models import Doctor, TipoUsuario
from ..schemas import DoctorCreate, DoctorResponse
from ..auth_utils import hash_password
from ..dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/doctores", tags=["doctores"])

def verificar_admin_o_administrativo(current_user: dict):
    if current_user["rol"] not in ["admin", "administrativo"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")

@router.get("/", response_model=List[DoctorResponse])
async def listar_doctores(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    verificar_admin_o_administrativo(current_user)
    stmt = select(Doctor)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=DoctorResponse, status_code=201)
async def crear_doctor(
    doctor_data: DoctorCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    verificar_admin_o_administrativo(current_user)
    stmt = select(Doctor).where(Doctor.email == doctor_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    tipo_doctor = await db.execute(select(TipoUsuario).where(TipoUsuario.nombre == "doctor"))
    tipo_id = tipo_doctor.scalar_one().id
    
    nuevo_doctor = Doctor(
        **doctor_data.dict(exclude={"password"}),
        password_hash=hash_password(doctor_data.password),
        tipo_usuario_id=tipo_id
    )
    db.add(nuevo_doctor)
    await db.commit()
    await db.refresh(nuevo_doctor)
    return nuevo_doctor

@router.put("/{doctor_id}", response_model=DoctorResponse)
async def actualizar_doctor(
    doctor_id: int,
    doctor_data: DoctorCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    verificar_admin_o_administrativo(current_user)
    stmt = select(Doctor).where(Doctor.id == doctor_id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    
    for key, value in doctor_data.dict(exclude={"password"}).items():
        setattr(doctor, key, value)
    if doctor_data.password:
        doctor.password_hash = hash_password(doctor_data.password)
    
    await db.commit()
    await db.refresh(doctor)
    return doctor

@router.delete("/{doctor_id}")
async def eliminar_doctor(
    doctor_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    verificar_admin_o_administrativo(current_user)
    stmt = select(Doctor).where(Doctor.id == doctor_id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")
    await db.delete(doctor)
    await db.commit()
    return {"message": "Doctor eliminado"}