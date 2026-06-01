"""
cita.me — Datos de prueba (seed)

Crea usuarios de ejemplo para los 4 roles con contrasenas hasheadas.
Ejecutar despues de que las tablas esten creadas.

Uso:
    from seed_data import seed_all
    await seed_all(session)
"""
from datetime import date, time, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Paciente, Doctor, Administrativo, Horario
from security import get_password_hash


def _fecha_futura(dias: int) -> date:
    return date.today() + timedelta(days=dias)


async def seed_all(session: AsyncSession):
    """Crea datos de prueba si no existen."""

    # ==========================================================================
    # PACIENTES
    # ==========================================================================
    stmt = select(Paciente).where(Paciente.documento == "1001234567")
    if not (await session.execute(stmt)).scalar_one_or_none():
        pacientes = [
            Paciente(
                nombre="Juan",
                apellido="Perez",
                documento="1001234567",
                email="juan.perez@test.com",
                telefono="3001234567",
                fecha_nacimiento=date(1990, 5, 15),
                password_hash=get_password_hash("1234"),
            ),
            Paciente(
                nombre="Maria",
                apellido="Lopez",
                documento="1007654321",
                email="maria.lopez@test.com",
                telefono="3007654321",
                fecha_nacimiento=date(1985, 8, 22),
                password_hash=get_password_hash("1234"),
            ),
            Paciente(
                nombre="Carlos",
                apellido="Rodriguez",
                documento="1009876543",
                email="carlos.rodriguez@test.com",
                telefono="3009876543",
                fecha_nacimiento=date(1995, 3, 10),
                password_hash=get_password_hash("1234"),
            ),
            Paciente(
                nombre="Mateo",
                apellido="Lopez",
                documento="20999888",
                email="mlopez@cotecnova.edu.co",
                telefono="300777666",
                fecha_nacimiento=date(2010, 11, 11),
                password_hash=get_password_hash("1234"),
            ),
        ]
        for p in pacientes:
            session.add(p)
        print("[SEED] Pacientes creados")

    # ==========================================================================
    # DOCTORES
    # ==========================================================================
    stmt = select(Doctor).where(Doctor.email == "maria.gonzalez@medicita.com")
    if not (await session.execute(stmt)).scalar_one_or_none():
        doctores = [
            Doctor(
                nombre="Maria",
                apellido="Gonzalez",
                especialidad="Cardiologia",
                email="maria.gonzalez@medicita.com",
                telefono="3001112222",
                activo=True,
                password_hash=get_password_hash("1234"),
            ),
            Doctor(
                nombre="Pedro",
                apellido="Martinez",
                especialidad="Dermatologia",
                email="pedro.martinez@medicita.com",
                telefono="3003334444",
                activo=True,
                password_hash=get_password_hash("1234"),
            ),
            Doctor(
                nombre="Ana",
                apellido="Castro",
                especialidad="Pediatria",
                email="ana.castro@medicita.com",
                telefono="3005556666",
                activo=True,
                password_hash=get_password_hash("1234"),
            ),
        ]
        for d in doctores:
            session.add(d)
        await session.flush()
        print("[SEED] Doctores creados")

    # ==========================================================================
    # ADMINISTRATIVOS
    # ==========================================================================
    stmt = select(Administrativo).where(Administrativo.email == "carlos@admin.com")
    if not (await session.execute(stmt)).scalar_one_or_none():
        administrativos = [
            Administrativo(
                nombre="Carlos",
                apellido="Sanchez",
                email="carlos@admin.com",
                telefono="3007778888",
                password_hash=get_password_hash("1234"),
                activo=True,
            ),
            Administrativo(
                nombre="Laura",
                apellido="Diaz",
                email="laura@admin.com",
                telefono="3009990000",
                password_hash=get_password_hash("1234"),
                activo=True,
            ),
        ]
        for a in administrativos:
            session.add(a)
        print("[SEED] Administrativos creados")

    # ==========================================================================
    # HORARIOS — fechas futuras relativas a hoy
    # Doctor 2 (Pedro Martinez, Dermatologia): horarios de manana 08-12
    # ==========================================================================
    stmt = select(Horario).where(Horario.doctor_id == 2)
    if not (await session.execute(stmt)).scalars().first():
        horarios = [
            Horario(doctor_id=2, fecha=_fecha_futura(1),  hora_inicio=time(8, 0), hora_fin=time(12, 0), activo=True),
            Horario(doctor_id=2, fecha=_fecha_futura(3),  hora_inicio=time(8, 0), hora_fin=time(12, 0), activo=True),
            Horario(doctor_id=2, fecha=_fecha_futura(5),  hora_inicio=time(8, 0), hora_fin=time(12, 0), activo=True),
            Horario(doctor_id=2, fecha=_fecha_futura(8),  hora_inicio=time(8, 0), hora_fin=time(12, 0), activo=True),
            Horario(doctor_id=2, fecha=_fecha_futura(10), hora_inicio=time(8, 0), hora_fin=time(12, 0), activo=True),
            Horario(doctor_id=3, fecha=_fecha_futura(2),  hora_inicio=time(9, 0), hora_fin=time(13, 0), activo=True),
            Horario(doctor_id=3, fecha=_fecha_futura(7),  hora_inicio=time(9, 0), hora_fin=time(13, 0), activo=True),
            Horario(doctor_id=1, fecha=_fecha_futura(4),  hora_inicio=time(7, 0), hora_fin=time(11, 0), activo=True),
            Horario(doctor_id=1, fecha=_fecha_futura(9),  hora_inicio=time(7, 0), hora_fin=time(11, 0), activo=True),
        ]
        for h in horarios:
            session.add(h)
        print("[SEED] Horarios creados")

    await session.commit()
    print("[SEED] Datos de prueba listos")


async def seed_if_empty(session: AsyncSession):
    """Verifica si la BD esta vacia y ejecuta el seed."""
    stmt = select(Paciente)
    result = await session.execute(stmt)
    if len(result.scalars().all()) == 0:
        await seed_all(session)
    else:
        print("[SEED] La base de datos ya tiene datos, omitiendo seed")


async def reset_passwords(session: AsyncSession):
    """Fuerza el re-hash de las contrasenas de todos los usuarios semilla."""
    hash_1234 = get_password_hash("1234")

    for email in ["maria.gonzalez@medicita.com", "pedro.martinez@medicita.com", "ana.castro@medicita.com"]:
        result = await session.execute(select(Doctor).where(Doctor.email == email))
        d = result.scalar_one_or_none()
        if d:
            d.password_hash = hash_1234
            print(f"[RESET] Doctor {email}")

    for email in ["carlos@admin.com", "laura@admin.com"]:
        result = await session.execute(select(Administrativo).where(Administrativo.email == email))
        a = result.scalar_one_or_none()
        if a:
            a.password_hash = hash_1234
            print(f"[RESET] Administrativo {email}")

    for doc in ["1001234567", "1007654321", "1009876543", "20999888"]:
        result = await session.execute(select(Paciente).where(Paciente.documento == doc))
        p = result.scalar_one_or_none()
        if p:
            p.password_hash = hash_1234
            print(f"[RESET] Paciente {doc}")

    await session.commit()
    print("[RESET] Contrasenas actualizadas")


if __name__ == "__main__":
    import asyncio
    import sys
    from database import AsyncSessionLocal, init_db

    async def main():
        await init_db()
        async with AsyncSessionLocal() as session:
            if "--reset-passwords" in sys.argv:
                await reset_passwords(session)
            else:
                await seed_all(session)

    asyncio.run(main())
