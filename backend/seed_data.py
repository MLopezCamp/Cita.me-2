"""
cita.me — Datos de prueba (seed)

Crea usuarios de ejemplo para los 4 roles con contrasenas hasheadas.
Ejecutar despues de que las tablas esten creadas.

Uso:
    from seed_data import seed_all
    await seed_all(session)
"""
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Paciente, Doctor, Administrativo
from security import get_password_hash


async def seed_all(session: AsyncSession):
    """Crea datos de prueba si no existen."""

    # ==========================================================================
    # PACIENTES
    # ==========================================================================
    stmt = select(Paciente).where(Paciente.documento == "1001234567")
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
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
        ]
        for p in pacientes:
            session.add(p)
        print("[SEED] Pacientes creados")

    # ==========================================================================
    # DOCTORES
    # ==========================================================================
    stmt = select(Doctor).where(Doctor.email == "maria.gonzalez@medicita.com")
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
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
        print("[SEED] Doctores creados")

    # ==========================================================================
    # ADMINISTRATIVOS (NUEVO)
    # ==========================================================================
    stmt = select(Administrativo).where(Administrativo.email == "carlos@admin.com")
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
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

    await session.commit()
    print("[SEED] Datos de prueba listos")


async def seed_if_empty(session: AsyncSession):
    """Verifica si la BD esta vacia y ejecuta el seed."""
    from models import Paciente
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

    for doc in ["1001234567", "1007654321", "1009876543"]:
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
