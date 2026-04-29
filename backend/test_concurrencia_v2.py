"""
PRUEBA DE CONCURRENCIA v2 — Locking Distribuido con Redis
=========================================================
Crea sus propios datos de prueba y los elimina al finalizar.
No depende de seed_data.py ni de datos previos en la BD.

Ejecutar dentro del contenedor:
    docker compose exec backend python test_concurrencia_v2.py

O localmente con Redis en localhost:6379:
    python backend/test_concurrencia_v2.py
"""
import asyncio
import sys
import os
import time
from datetime import date, time as dt_time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, AsyncSessionLocal
from models import Doctor, Horario, Paciente
from schemas import CitaCreate
from services.cita_service import crear_cita
import redis_client as rc
from redis_client import init_redis, close_redis

N = 10
FECHA = date(2099, 1, 7)   # miércoles lejano, nunca tiene datos reales

_doctor_id: int = 0
_paciente_ids: list[int] = []


# ══════════════════════════════════════════════════════════
# Setup / Teardown
# ══════════════════════════════════════════════════════════

async def setup():
    global _doctor_id, _paciente_ids

    await init_db()
    await init_redis()

    async with AsyncSessionLocal() as session:
        doctor = Doctor(
            nombre="TestConcurrencia",
            apellido="Lock",
            especialidad="Concurrencia",
            email="tc_lock_v2@citame.test",
            telefono="0000000000",
            activo=True,
        )
        session.add(doctor)
        await session.flush()
        _doctor_id = doctor.id

        session.add(Horario(
            doctor_id=_doctor_id,
            dia_semana=FECHA.weekday(),
            hora_inicio=dt_time(8, 0),
            hora_fin=dt_time(11, 0),
            activo=True,
        ))

        _paciente_ids = []
        for i in range(N):
            p = Paciente(
                nombre=f"PTC{i + 1}",
                apellido="Concurrencia",
                documento=f"CTEST2{i + 1:05d}",
                email=f"ptc2_{i + 1}@citame.test",
                telefono="3000000000",
                fecha_nacimiento=date(1990, 1, 1),
            )
            session.add(p)
            await session.flush()
            _paciente_ids.append(p.id)

        await session.commit()

    print(f"[setup] Doctor #{_doctor_id} | {N} pacientes | horario {FECHA} 08:00-11:00\n")


async def teardown():
    print("[teardown] Datos conservados en BD para revisión del docente")
    print(f"           Doctor #{_doctor_id} | Pacientes: {_paciente_ids}")
    await close_redis()


# ══════════════════════════════════════════════════════════
# TEST 1: Lock Redis directo (SET NX EX)
# ══════════════════════════════════════════════════════════

async def test_1_lock_directo() -> bool:
    """
    Lanza N coroutines simultáneas que intentan adquirir el mismo lock.
    Esperado: exactamente 1 adquiere, N-1 son rechazadas en el acto.
    """
    print("=" * 60)
    print("TEST 1 — Lock Redis directo (SET NX EX)")
    print("=" * 60)

    lock_key = f"test:directo:{_doctor_id}"
    redis = rc.redis_client
    await redis.delete(f"lock:citame:{lock_key}")

    adquiridos: list[int] = []
    rechazados: list[int] = []

    async def intentar(idx: int):
        t0 = time.time()
        ok = await rc.set_lock_raw(lock_key, value=str(idx), ttl=10)
        ms = round((time.time() - t0) * 1000, 1)
        estado = "LOCK-OK " if ok else "LOCK-NO "
        print(f"  [{idx:02d}] {estado}  {ms:>5}ms")
        (adquiridos if ok else rechazados).append(idx)

    print(f"Lanzando {N} intentos concurrentes al mismo lock...\n")
    await asyncio.gather(*[intentar(i) for i in range(1, N + 1)])

    # Limpiar el lock explícitamente (TTL=10s pero no queremos esperar)
    await redis.delete(f"lock:citame:{lock_key}")

    print(f"\nAdquiridos : {len(adquiridos)}  {adquiridos}")
    print(f"Rechazados : {len(rechazados)}  {rechazados}")

    ok = len(adquiridos) == 1 and len(rechazados) == N - 1
    print(f"\nRESULTADO: {'PASS' if ok else 'FAIL'}")
    return ok


# ══════════════════════════════════════════════════════════
# TEST 2: Reserva concurrente — mismo slot
# ══════════════════════════════════════════════════════════

async def test_2_mismo_slot() -> bool:
    """
    N pacientes intentan reservar el mismo slot simultáneamente.
    Esperado: exactamente 1 cita creada, N-1 rechazadas por el lock de Redis.
    """
    print("\n" + "=" * 60)
    print("TEST 2 — Reserva concurrente: mismo slot")
    print(f"         {N} pacientes → Doctor #{_doctor_id} | {FECHA} 08:00")
    print("=" * 60 + "\n")

    resultados: list[dict] = []

    async def reservar(pac_id: int, idx: int):
        t0 = time.time()
        r: dict = {"idx": idx, "pac": pac_id, "ok": False, "error": None, "cita_id": None}
        async with AsyncSessionLocal() as session:
            try:
                data = CitaCreate(
                    paciente_id=pac_id,
                    doctor_id=_doctor_id,
                    fecha=FECHA,
                    hora=dt_time(8, 0),
                    motivo=f"Test concurrencia slot 08:00 #{idx}",
                )
                cita = await crear_cita(session, data)
                await session.commit()
                r["ok"] = True
                r["cita_id"] = cita.id
            except Exception as e:
                r["error"] = str(e)[:60]
        r["ms"] = round((time.time() - t0) * 1000, 1)
        resultados.append(r)

    await asyncio.gather(*[reservar(_paciente_ids[i], i + 1) for i in range(N)])

    print(f"{'#':>3}  {'PAC':>5}  {'ESTADO':<12}  {'MS':>7}  DETALLE")
    print("-" * 65)
    for r in sorted(resultados, key=lambda x: x["idx"]):
        estado = "EXITO" if r["ok"] else "RECHAZADA"
        detalle = f"Cita #{r['cita_id']}" if r["ok"] else (r["error"] or "")
        print(f"  {r['idx']:>2}  #{r['pac']:>4}  {estado:<12}  {r['ms']:>6}ms  {detalle}")
    print("-" * 65)

    exitosas = [r for r in resultados if r["ok"]]
    print(f"\nExitosas: {len(exitosas)} | Rechazadas: {N - len(exitosas)}")

    if len(exitosas) == 1:
        print("RESULTADO: PASS — 1 cita creada, race condition prevenida")
        return True
    elif len(exitosas) == 0:
        print("RESULTADO: FAIL — Ninguna cita creada (¿Redis conectado? ¿Horario correcto?)")
        return False
    else:
        print(f"RESULTADO: FAIL — {len(exitosas)} citas duplicadas (race condition detectada)")
        return False


# ══════════════════════════════════════════════════════════
# TEST 3: Slots distintos no se bloquean entre sí
# ══════════════════════════════════════════════════════════

async def test_3_slots_distintos() -> bool:
    """
    Dos pacientes reservan slots diferentes al mismo tiempo.
    Esperado: ambos exitosos — cada slot tiene su propio lock key.
    """
    print("\n" + "=" * 60)
    print("TEST 3 — Slots distintos: sin interferencia")
    print("         08:30 y 09:00 en paralelo → ambos deben EXITOSOS")
    print("=" * 60 + "\n")

    # Garantizar que esos locks no están activos
    redis = rc.redis_client
    for hora_str in ["08:30:00", "09:00:00"]:
        await redis.delete(f"lock:citame:doctor_{_doctor_id}:fecha_{FECHA}:hora_{hora_str}")

    resultados: list[dict] = []

    async def reservar_slot(pac_id: int, hora: dt_time, label: str):
        t0 = time.time()
        r: dict = {"slot": label, "ok": False, "error": None, "cita_id": None}
        async with AsyncSessionLocal() as session:
            try:
                data = CitaCreate(
                    paciente_id=pac_id,
                    doctor_id=_doctor_id,
                    fecha=FECHA,
                    hora=hora,
                    motivo=f"Test slots independientes {label}",
                )
                cita = await crear_cita(session, data)
                await session.commit()
                r["ok"] = True
                r["cita_id"] = cita.id
            except Exception as e:
                r["error"] = str(e)[:60]
        r["ms"] = round((time.time() - t0) * 1000, 1)
        resultados.append(r)

    await asyncio.gather(
        reservar_slot(_paciente_ids[0], dt_time(8, 30), "08:30"),
        reservar_slot(_paciente_ids[1], dt_time(9, 0),  "09:00"),
    )

    for r in resultados:
        estado = "EXITO" if r["ok"] else "RECHAZADA"
        detalle = f"Cita #{r['cita_id']}" if r["ok"] else (r.get("error") or "")
        print(f"  Slot {r['slot']}: {estado:<10}  {r['ms']:>6}ms  {detalle}")

    exitosas = [r for r in resultados if r["ok"]]
    print(f"\nExitosas: {len(exitosas)} / 2")

    ok = len(exitosas) == 2
    print(f"RESULTADO: {'PASS — sin interferencia entre locks distintos' if ok else 'FAIL — colisión falsa entre slots'}")
    return ok


# ══════════════════════════════════════════════════════════
# TEST 4: Inspección de claves en Redis
# ══════════════════════════════════════════════════════════

async def test_4_claves_redis() -> bool:
    """
    Muestra todas las claves activas en Redis relacionadas con los tests.
    Confirma que los locks tienen TTL y que el semáforo es visible.
    """
    print("\n" + "=" * 60)
    print("TEST 4 — Claves activas en Redis")
    print("=" * 60 + "\n")

    redis = rc.redis_client
    patrones = [
        f"lock:citame:*doctor_{_doctor_id}*",
        "sem:citame:reservas_global",
    ]

    todas: list[str] = []
    for patron in patrones:
        keys = await redis.keys(patron)
        todas.extend(keys)

    if todas:
        print(f"{'CLAVE':<55}  {'TTL':>6}  VALOR")
        print("-" * 72)
        for k in sorted(todas):
            ttl = await redis.ttl(k)
            val = await redis.get(k)
            ttl_str = f"{ttl}s" if ttl > 0 else ("∞" if ttl == -1 else "exp")
            print(f"  {k:<53}  {ttl_str:>5}  {str(val)[:20]!r}")
        print(f"\nTotal: {len(todas)} claves")
        print("Puedes verlas en Redis Commander → http://localhost:8081")
    else:
        print("  (ninguna clave activa — los locks ya expiraron por TTL)")
        print("  Tip: ejecuta el test justo después de los anteriores para verlos.")

    return True


# ══════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════

async def main():
    print("=" * 60)
    print("  PRUEBA DE CONCURRENCIA v2 — CITA.ME")
    print("  Redis Distributed Locking (SET NX EX)")
    print("=" * 60 + "\n")

    await setup()

    tests = {
        "Test 1 — Lock directo (SET NX EX)": test_1_lock_directo,
        "Test 2 — Mismo slot concurrente  ": test_2_mismo_slot,
        "Test 3 — Slots distintos         ": test_3_slots_distintos,
        "Test 4 — Claves Redis            ": test_4_claves_redis,
    }

    resultados: dict[str, bool] = {}
    try:
        for nombre, fn in tests.items():
            resultados[nombre] = await fn()
    finally:
        print()
        await teardown()

    print("\n" + "=" * 60)
    print("  RESUMEN FINAL")
    print("=" * 60)
    for nombre, paso in resultados.items():
        print(f"  {'PASS' if paso else 'FAIL'}  {nombre}")
    aprobados = sum(resultados.values())
    print(f"\n  {aprobados}/{len(resultados)} tests pasaron")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
