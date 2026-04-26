"""
Script de inicialización de datos de prueba.
Ejecutar: python seed_data.py
"""
import asyncio
import sys
import os
from datetime import date, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, AsyncSessionLocal
from models import Doctor, Horario, Paciente


DOCTORES = [
    {
        "nombre": "María",
        "apellido": "González",
        "especialidad": "Medicina General",
        "email": "maria.gonzalez@medicita.com",
        "telefono": "3001234567",
    },
    {
        "nombre": "Carlos",
        "apellido": "Ramírez",
        "especialidad": "Cardiología",
        "email": "carlos.ramirez@medicita.com",
        "telefono": "3002345678",
    },
    {
        "nombre": "Ana",
        "apellido": "López",
        "especialidad": "Dermatología",
        "email": "ana.lopez@medicita.com",
        "telefono": "3003456789",
    },
    {
        "nombre": "Roberto",
        "apellido": "Martínez",
        "especialidad": "Pediatría",
        "email": "roberto.martinez@medicita.com",
        "telefono": "3004567890",
    },
    {
        "nombre": "Laura",
        "apellido": "Hernández",
        "especialidad": "Neurología",
        "email": "laura.hernandez@medicita.com",
        "telefono": "3005678901",
    },
]

HORARIOS = [
    (0, 0, "08:00", "12:00"),
    (0, 0, "14:00", "17:00"),
    (0, 1, "08:00", "12:00"),
    (0, 2, "08:00", "12:00"),
    (0, 3, "08:00", "12:00"),
    (0, 4, "08:00", "12:00"),
    (1, 0, "09:00", "13:00"),
    (1, 2, "09:00", "13:00"),
    (1, 4, "09:00", "13:00"),
    (2, 1, "08:00", "12:00"),
    (2, 3, "08:00", "12:00"),
    (2, 5, "08:00", "14:00"),
    (3, 0, "08:00", "12:00"),
    (3, 1, "14:00", "18:00"),
    (3, 3, "08:00", "12:00"),
    (3, 4, "08:00", "12:00"),
    (4, 1, "09:00", "13:00"),
    (4, 3, "09:00", "13:00"),
    (4, 5, "09:00", "13:00"),
]

PACIENTES = [
    {
        "nombre": "Juan",
        "apellido": "Pérez",
        "documento": "1001234567",
        "email": "juan.perez@email.com",
        "telefono": "3101112233",
        "fecha_nacimiento": date(1990, 5, 15),
    },
    {
        "nombre": "Camila",
        "apellido": "Torres",
        "documento": "1007654321",
        "email": "camila.torres@email.com",
        "telefono": "3102223344",
        "fecha_nacimiento": date(1985, 11, 22),
    },
    {
        "nombre": "Andrés",
        "apellido": "Morales",
        "documento": "1009876543",
        "email": "andres.morales@email.com",
        "telefono": "3103334455",
        "fecha_nacimiento": date(1978, 3, 10),
    },
    {
        "nombre": "Valentina",
        "apellido": "Díaz",
        "documento": "1005432167",
        "email": "valentina.diaz@email.com",
        "telefono": "3104445566",
        "fecha_nacimiento": date(1995, 8, 30),
    },
    {
        "nombre": "Pedro",
        "apellido": "Castillo",
        "documento": "1003210987",
        "email": "pedro.castillo@email.com",
        "telefono": "3105556677",
        "fecha_nacimiento": date(2000, 1, 18),
    },
    {
        "nombre": "Sofía",
        "apellido": "Vargas",
        "documento": "1006789012",
        "email": "sofia.vargas@email.com",
        "telefono": "3106667788",
        "fecha_nacimiento": date(1992, 12, 5),
    },
    {
        "nombre": "Diego",
        "apellido": "Ruiz",
        "documento": "1008901234",
        "email": "diego.ruiz@email.com",
        "telefono": "3107778899",
        "fecha_nacimiento": date(1988, 7, 14),
    },
    {
        "nombre": "Isabella",
        "apellido": "Ortiz",
        "documento": "1004567890",
        "email": "isabella.ortiz@email.com",
        "telefono": "3108889900",
        "fecha_nacimiento": date(1997, 4, 25),
    },
]


async def seed():
    print("=" * 50)
    print("  SEMBRANDO DATOS DE PRUEBA")
    print("=" * 50)

    await init_db()

    async with AsyncSessionLocal() as session:
        try:
            # ── Doctores ──
            print("\n[1/3] Creando doctores...")
            doctores_creados = []
            for doc_data in DOCTORES:
                doctor = Doctor(**doc_data)
                session.add(doctor)
                doctores_creados.append(doctor)

            await session.flush()
            print(f"      ✓ {len(doctores_creados)} doctores creados")
            for d in doctores_creados:
                print(f"        - Dr. {d.nombre} {d.apellido} ({d.especialidad})")

            # ── Horarios ──
            print("\n[2/3] Creando horarios...")
            horarios_creados = 0
            for doctor_idx, dia, h_inicio, h_fin in HORARIOS:
                horario = Horario(
                    doctor_id=doctores_creados[doctor_idx].id,
                    dia_semana=dia,
                    hora_inicio=time.fromisoformat(h_inicio),
                    hora_fin=time.fromisoformat(h_fin),
                    activo=True,
                )
                session.add(horario)
                horarios_creados += 1

            await session.flush()
            print(f"      ✓ {horarios_creados} horarios creados")

            # ── Pacientes ──
            print("\n[3/3] Creando pacientes...")
            for pac_data in PACIENTES:
                paciente = Paciente(**pac_data)
                session.add(paciente)

            await session.flush()
            print(f"      ✓ {len(PACIENTES)} pacientes creados")
            for p in PACIENTES:
                print(f"        - {p['nombre']} {p['apellido']} ({p['documento']})")

            await session.commit()

            print("\n" + "=" * 50)
            print("  DATOS SEMBRADOS EXITOSAMENTE")
            print("=" * 50)
            print(f"  Doctores:  {len(doctores_creados)}")
            print(f"  Horarios:  {horarios_creados}")
            print(f"  Pacientes: {len(PACIENTES)}")
            print("=" * 50)

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())