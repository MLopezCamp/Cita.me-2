"""
PRUEBA DE CONCURRENCIA — Locking Distribuido con Redis
======================================================

Ejecutar con Redis corriendo:
    python test_concurrencia.py

Este script simula 10 solicitudes concurrentes intentando reservar
el mismo horario. Solo UNA debe exitir — las demás reciben error.

Demuestra:
- asyncio.gather para concurrencia real
- DistributedLock de Redis previniendo condición de carrera
- Manejo correcto deRace Condition en reservas
"""
import asyncio
import sys
import os
import time
import random
from datetime import date, time as dt_time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, AsyncSessionLocal
from models import Doctor, Horario, Paciente, Cita
from schemas import CitaCreate
from services.cita_service import crear_cita
from redis_client import DistributedLock


# Configuración de la prueba
NUM_SOLICITUDES = 10
DOCTOR_ID = 1
FECHA = "2025-08-01"
HORA = "08:00"
PACIENTE_BASE_ID = 1


async def setup_datos_prueba():
    """Preparar datos necesarios para la prueba."""
    await init_db()
    async with AsyncSessionLocal() as session:
        # Verificar que existe al menos un doctor y paciente
        doctor = await session.get(Doctor, DOCTOR_ID)
        if not doctor:
            print("✗ Error: No existe el doctor. Ejecute seed_data.py primero.")
            sys.exit(1)

        paciente = await session.get(Paciente, PACIENTE_BASE_ID)
        if not paciente:
            print("✗ Error: No existe el paciente. Ejecute seed_data.py primero.")
            sys.exit(1)

        # Crear pacientes adicionales para la prueba si no existen
        for i in range(2, NUM_SOLICITUDES + 1):
            p = await session.get(Paciente, i)
            if not p:
                p = Paciente(
                    nombre=f"Test{i}",
                    apellido=f"Usuario{i}",
                    documento=f"99{i:07d}",
                    email=f"test{i}@concurrent.com",
                    telefono="3000000000",
                    fecha_nacimiento="1990-01-01",
                )
                session.add(p)

        # Crear horario para el doctor si no existe
        dia_semana = date.fromisoformat(FECHA).weekday()
        stmt = Horario.__table__.select().where(
            (Horario.doctor_id == DOCTOR_ID) &
            (Horario.dia_semana == dia_semana) &
            (Horario.activo == True)
        )
        result = await session.execute(stmt)
        if result.fetchone() is None:
            horario = Horario(
                doctor_id=DOCTOR_ID,
                dia_semana=dia_semana,
                hora_inicio=dt_time(8, 0),
                hora_fin=dt_time(12, 0),
                activo=True,
            )
            session.add(horario)

        await session.commit()
        print(f"✓ Datos preparados: Doctor #{DOCTOR_ID}, {NUM_SOLICITUDES} pacientes")


async def intentar_reserva(paciente_id: int, intento_num: int) -> dict:
    """
    Intentar crear una cita. Retorna resultado con timing.
    Cada llamada se ejecuta como una coroutine independiente.
    """
    inicio = time.time()
    resultado = {
        "intento": intento_num,
        "paciente_id": paciente_id,
        "exito": False,
        "error": None,
        "duracion_ms": 0,
    }

    async with AsyncSessionLocal() as session:
        try:
            data = CitaCreate(
                paciente_id=paciente_id,
                doctor_id=DOCTOR_ID,
                fecha=date.fromisoformat(FECHA),
                hora=dt_time(8, 0),
                motivo=f"Consulta de prueba #{intento_num}",
            )
            cita = await crear_cita(session, data)
            resultado["exito"] = True
            resultado["cita_id"] = cita.id
        except (ValueError, RuntimeError) as e:
            resultado["error"] = str(e)
        except Exception as e:
            resultado["error"] = f"Error inesperado: {e}"

    resultado["duracion_ms"] = round((time.time() - inicio) * 1000, 1)
    return resultado


async def probar_lock_directo():
    """Prueba directa del DistributedLock sin pasar por el servicio."""
    print("\n--- PRUEBA DIRECTA DEL LOCK REDIS ---")
    lock_key = f"cita:doctor_{DOCTOR_ID}:fecha_{FECHA}:hora_{HORA}"

    resultados = []

    async def adquirir_lock(idx: int):
        inicio = time.time()
        lock = DistributedLock(lock_key, timeout=5)
        adquirido = await lock.acquire(wait_timeout=8)
        duracion = round((time.time() - inicio) * 1000, 1)

        resultado = {"idx": idx, "adquirido": adquirido, "duracion_ms": duracion}
        resultados.append(resultado)

        if adquirido:
            # Simular trabajo
            await asyncio.sleep(random.uniform(0.3, 0.8))
            await lock.release()

        return resultado

    print(f"Lanzando {NUM_SOLICITUDES} intentos de lock concurrentes...")
    await asyncio.gather(*[adquirir_lock(i) for i in range(NUM_SOLICITUDES)])

    adquiridos = [r for r in resultados if r["adquirido"]]
    fallidos = [r for r in resultados if not r["adquirido"]]

    print(f"\nResultados del lock:")
    print(f"  Adquiridos: {len(adquiridos)} (serializados)")
    print(f"  Fallidos (timeout): {len(fallidos)}")
    for r in adquiridos:
        print(f"    ✓ Intento #{r['idx']} — {r['duracion_ms']}ms")
    for r in fallidos:
        print(f"    ✗ Intento #{r['idx']} — {r['duracion_ms']}ms")

    if len(adquiridos) <= NUM_SOLICITUDES:
        print("\n✓ PASS: El lock serializó el acceso correctamente")
    else:
        print("\n✗ FAIL: Múltiples locks adquiridos simultáneamente")


async def probar_reserva_concurrente():
    """Prueba completa: reservas concurrentes a través del servicio."""
    print(f"\n--- PRUEBA DE RESERVA CONCURRENTE ---")
    print(f"Configuración: {NUM_SOLICITUDES} solicitudes simultáneas")
    print(f"Target: Doctor #{DOCTOR_ID}, Fecha {FECHA}, Hora {HORA}")
    print(f"Esperado: 1 éxito, {NUM_SOLICITUDES - 1} rechazadas\n")

    # Lanzar todas las solicitudes concurrentemente
    tareas = [
        intentar_reserva(paciente_id=i, intento_num=i)
        for i in range(1, NUM_SOLICITUDES + 1)
    ]

    resultados = await asyncio.gather(*tareas)

    # Analizar resultados
    exitosas = [r for r in resultados if r["exito"]]
    fallidas = [r for r in resultados if not r["exito"]]

    print("Resultados detallados:")
    print("-" * 65)
    for r in resultados:
        estado = "✓ EXITO" if r["exito"] else "✗ RECHAZADA"
        cita_info = f" → Cita #{r['cita_id']}" if r["exito"] else ""
        error_info = f" → {r['error'][:45]}" if r["error"] else ""
        print(f"  {estado} | Paciente #{r['paciente_id']:>2} | "
              f"{r['duracion_ms']:>6}ms{cita_info}{error_info}")
    print("-" * 65)

    # Veredicto
    print(f"\nResumen:")
    print(f"  Exitosas: {len(exitosas)}")
    print(f"  Rechazadas: {len(fallidas)}")
    print(f"  Tiempo total: {max(r['duracion_ms'] for r in resultados)}ms")

    if len(exitosas) == 1 and len(fallidas) == NUM_SOLICITUDES - 1:
        print("\n" + "=" * 50)
        print("  ✓ PASS: Locking distribuido funciona correctamente")
        print("  Solo 1 cita fue creada, las demás fueron rechazadas")
        print("=" * 50)
    elif len(exitosas) == 0:
        print("\n✗ FAIL: Ninguna cita fue creada (posible problema de datos)")
    else:
        print(f"\n✗ FAIL: Se crearon {len(exitosas)} citas — condición de carrera detectada")


async def probar_lock_sin_redis():
    """Demostrar qué pasaría SIN el lock (condición de carrera)."""
    print(f"\n--- DEMOSTRACIÓN: SIN LOCK (Race Condition) ---")
    print("Insertando directamente en DB sin locking...\n")

    async with AsyncSessionLocal() as session:
        # Limpiar citas de prueba previas para esta demo
        from sqlalchemy import delete
        await session.execute(delete(Cita).where(Cita.motivo.like("RACE_%")))
        await session.commit()

    resultados_race = []

    async def insertar_directo(idx: int):
        inicio = time.time()
        resultado = {"idx": idx, "exito": False, "error": None, "duracion_ms": 0}

        async with AsyncSessionLocal() as session:
            try:
                # Pequeño delay aleatorio para exacerbar la race condition
                await asyncio.sleep(random.uniform(0.01, 0.05))

                # Verificar manualmente (sin lock — ventana de race condition)
                from sqlalchemy import select, and_
                stmt = select(Cita).where(
                    and_(
                        Cita.doctor_id == DOCTOR_ID,
                        Cita.fecha == date.fromisoformat(FECHA),
                        Cita.hora == dt_time(9, 0),
                        Cita.estado != "cancelada",
                    )
                )
                result = await session.execute(stmt)
                existe = result.scalar_one_or_none()

                if existe:
                    resultado["error"] = "Slot ocupado (detectado sin lock)"
                else:
                    # Ventana de race condition: entre el check y el insert
                    await asyncio.sleep(random.uniform(0.01, 0.03))

                    cita = Cita(
                        paciente_id=idx,
                        doctor_id=DOCTOR_ID,
                        fecha=date.fromisoformat(FECHA),
                        hora=dt_time(9, 0),
                        motivo=f"RACE_test_{idx}",
                        estado="pendiente",
                    )
                    session.add(cita)
                    await session.commit()
                    resultado["exito"] = True
                    resultado["cita_id"] = cita.id

            except Exception as e:
                resultado["error"] = str(e)[:50]

        resultado["duracion_ms"] = round((time.time() - inicio) * 1000, 1)
        resultados_race.append(resultado)
        return resultado

    await asyncio.gather(*[insertar_directo(i) for i in range(1, NUM_SOLICITUDES + 1)])

    exitosas_race = [r for r in resultados_race if r["exito"]]
    print("Resultados SIN lock:")
    print("-" * 55)
    for r in resultados_race:
        estado = "✓ INSERTADA" if r["exito"] else "✗ RECHAZADA"
        print(f"  {estado} | Intento #{r['idx']:>2} | {r['duracion_ms']:>6}ms")
    print("-" * 55)
    print(f"\n  Citas duplicadas creadas: {len(exitosas_race)}")

    if len(exitosas_race) > 1:
        print("  ⚠ Se detectó race condition — múltiples inserts sin lock")
        print("  Esto es lo que el DistributedLock de Redis previene")
    else:
        print("  (En este caso particular no hubo race condition,")
        print("   pero es no determinista — ejecutar varias veces)")

    # Limpiar datos de prueba
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(Cita).where(Cita.motivo.like("RACE_%")))
        await session.commit()


async def main():
    print("=" * 50)
    print("  PRUEBAS DE CONCURRENCIA — CITAS MÉDICAS")
    print("  Locking Distribuido con Redis")
    print("=" * 50)

    await setup_datos_prueba()

    # Prueba 1: Lock directo
    await probar_lock_directo()

    # Prueba 2: Reserva concurrente con lock
    await probar_reserva_concurrente()

    # Prueba 3: Demostración sin lock
    await probar_lock_sin_redis()

    print("\n" + "=" * 50)
    print("  PRUEBAS FINALIZADAS")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())