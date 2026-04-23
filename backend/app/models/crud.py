from sqlalchemy.orm import Session
from . import database, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_paciente(db: Session, paciente_id: int):
    return db.query(database.Paciente).filter(database.Paciente.id == paciente_id).first()

def get_paciente_by_documento(db: Session, documento: str):
    return db.query(database.Paciente).filter(database.Paciente.documento == documento).first()

def create_paciente(db: Session, paciente: schemas.PacienteCreate):
    db_paciente = database.Paciente(**paciente.dict())
    db.add(db_paciente)
    db.commit()
    db.refresh(db_paciente)
    return db_paciente

def get_medico(db: Session, medico_id: int):
    return db.query(database.Medico).filter(database.Medico.id == medico_id).first()

def get_medicos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(database.Medico).offset(skip).limit(limit).all()

def create_medico(db: Session, medico: schemas.MedicoCreate):
    db_medico = database.Medico(**medico.dict())
    db.add(db_medico)
    db.commit()
    db.refresh(db_medico)
    return db_medico

def update_medico(db: Session, medico_id: int, medico: schemas.MedicoCreate):
    db_medico = get_medico(db, medico_id)
    if db_medico:
        for key, value in medico.dict().items():
            setattr(db_medico, key, value)
        db.commit()
        db.refresh(db_medico)
    return db_medico

def delete_medico(db: Session, medico_id: int):
    db_medico = get_medico(db, medico_id)
    if db_medico:
        db.delete(db_medico)
        db.commit()
    return db_medico

def get_horarios_by_medico(db: Session, medico_id: int):
    return db.query(database.Horario).filter(database.Horario.medico_id == medico_id).all()

def create_horario(db: Session, horario: schemas.HorarioCreate):
    db_horario = database.Horario(**horario.dict())
    db.add(db_horario)
    db.commit()
    db.refresh(db_horario)
    return db_horario

def delete_horario(db: Session, horario_id: int):
    db_horario = db.query(database.Horario).filter(database.Horario.id == horario_id).first()
    if db_horario:
        db.delete(db_horario)
        db.commit()
    return db_horario

def create_cita(db: Session, cita: schemas.CitaCreate):
    db_cita = database.Cita(**cita.dict())
    db.add(db_cita)
    db.commit()
    db.refresh(db_cita)
    return db_cita

def get_cita(db: Session, cita_id: int):
    return db.query(database.Cita).filter(database.Cita.id == cita_id).first()

def get_citas_by_paciente(db: Session, paciente_id: int):
    return db.query(database.Cita).filter(database.Cita.paciente_id == paciente_id).all()

def get_citas_by_medico(db: Session, medico_id: int):
    return db.query(database.Cita).filter(database.Cita.medico_id == medico_id).all()

def cancelar_cita(db: Session, cita_id: int):
    db_cita = get_cita(db, cita_id)
    if db_cita:
        db_cita.estado = database.EstadoCita.cancelada
        db.commit()
        db.refresh(db_cita)
    return db_cita

def get_administrador_by_usuario(db: Session, usuario: str):
    return db.query(database.Administrador).filter(database.Administrador.usuario == usuario).first()

def create_administrador(db: Session, usuario: str, password: str):
    hashed = pwd_context.hash(password)
    db_admin = database.Administrador(usuario=usuario, password_hash=hashed)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin