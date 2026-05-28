from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_session
from ..models import Paciente, TipoUsuario
from ..schemas import PacienteCreate, PacienteResponse
from ..auth_utils import hash_password
from ..dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

def verificar_admin_o_administrativo(current_user: dict):
    if current_user["rol"] not in ["admin", "administrativo"]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes")

@router.get("/", response_model=List[PacienteResponse])
async def listar_pacientes(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    verificar_admin_o_administrativo(current_user)
    stmt = select(Paciente)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{paciente_id}", response_model=PacienteResponse)
async def obtener_paciente(
    paciente_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if current_user["rol"] == "paciente" and int(current_user["sub"]) != paciente_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    if current_user["rol"] not in ["admin", "administrativo"] and current_user["rol"] != "paciente":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    stmt = select(Paciente).where(Paciente.id == paciente_id)
    result = await db.execute(stmt)
    paciente = result.scalar_one_or_none()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@router.post("/", response_model=PacienteResponse, status_code=201)
async def crear_paciente(
    paciente_data: PacienteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    # Solo admin o administrativo pueden crear pacientes directamente
    verificar_admin_o_administrativo(current_user)
    
    stmt = select(Paciente).where((Paciente.email == paciente_data.email) | (Paciente.documento == paciente_data.documento))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email o documento ya registrado")
    
    tipo_paciente = await db.execute(select(TipoUsuario).where(TipoUsuario.nombre == "paciente"))
    tipo_id = tipo_paciente.scalar_one().id
    
    nuevo_paciente = Paciente(
        **paciente_data.dict(exclude={"password"}),
        password_hash=hash_password(paciente_data.password),
        tipo_usuario_id=tipo_id
    )
    db.add(nuevo_paciente)
    await db.commit()
    await db.refresh(nuevo_paciente)
    return nuevo_paciente

@router.put("/{paciente_id}", response_model=PacienteResponse)
async def actualizar_paciente(
    paciente_id: int,
    paciente_data: PacienteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if current_user["rol"] == "paciente" and int(current_user["sub"]) != paciente_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    if current_user["rol"] not in ["admin", "administrativo"] and current_user["rol"] != "paciente":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    stmt = select(Paciente).where(Paciente.id == paciente_id)
    result = await db.execute(stmt)
    paciente = result.scalar_one_or_none()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    for key, value in paciente_data.dict(exclude={"password"}).items():
        setattr(paciente, key, value)
    if paciente_data.password:
        paciente.password_hash = hash_password(paciente_data.password)
    
    await db.commit()
    await db.refresh(paciente)
    return paciente