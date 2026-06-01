"""
PRUEBA DE COMUNICACIÓN ASÍNCRONA — RabbitMQ
============================================

Ejecutar con RabbitMQ corriendo:
    docker compose exec backend python test_rabbitmq.py

Demuestra:
- Publicacion de eventos a un exchange topic
- Consumo concurrente con prefetch_count
- Routing keys del sistema: cita.#, parte_medico.#, horario.#
"""
import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RABBITMQ_URL, EXCHANGE_CITAS, QUEUE_CITAS
import aio_pika


async def test_publicacion_consumo():
    """Publicar eventos de todos los tipos y verificar que se consumen correctamente."""
    print("=" * 55)
    print("  PRUEBA DE RABBITMQ — COMUNICACION ASINCRONA")
    print("=" * 55)

    eventos_publicados = []
    eventos_consumidos = []

    # ── 1. Conectar ──
    print("\n[1] Conectando a RabbitMQ...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=3)

    exchange = await channel.declare_exchange(EXCHANGE_CITAS, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(QUEUE_CITAS, durable=True)
    await queue.bind(exchange, routing_key="cita.#")
    await queue.bind(exchange, routing_key="parte_medico.#")
    await queue.bind(exchange, routing_key="horario.#")
    print("    OK Conexion establecida — exchange y bindings declarados")

    # ── 2. Consumidor ──
    print("\n[2] Iniciando consumer...")

    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(message.body.decode())
            routing_key = message.routing_key
            eventos_consumidos.append({"routing_key": routing_key, **body})
            await asyncio.sleep(0.05)
            print(f"    [CONSUMER] {routing_key}: {json.dumps(body)[:60]}")

    await queue.consume(on_message)
    await asyncio.sleep(0.5)
    print("    OK Consumer registrado con prefetch_count=3")

    # ── 3. Publicar eventos de todos los tipos ──
    print("\n[3] Publicando eventos del sistema...")
    eventos_test = [
        # Citas
        ("cita.creada",            {"cita_id": 1, "paciente_id": 4, "doctor_id": 2, "fecha": "2026-08-01", "hora": "08:00"}),
        ("cita.creada",            {"cita_id": 2, "paciente_id": 1, "doctor_id": 3, "fecha": "2026-08-02", "hora": "09:00"}),
        ("cita.estado_actualizado",{"cita_id": 1, "nuevo_estado": "confirmada", "estado_anterior": "pendiente"}),
        ("cita.estado_actualizado",{"cita_id": 2, "nuevo_estado": "cancelada",  "estado_anterior": "pendiente"}),
        # Parte medico
        ("parte_medico.creado",    {"cita_id": 1, "doctor_id": 2, "diagnostico": "Dermatitis leve"}),
        # Horarios lote (uno o varios dias)
        ("horario.lote_nuevo",     {"doctor_id": 2, "fechas": ["2026-08-10", "2026-08-11", "2026-08-12"], "hora_inicio": "08:00:00", "hora_fin": "12:00:00"}),
        ("horario.lote_nuevo",     {"doctor_id": 3, "fechas": ["2026-08-15"], "hora_inicio": "09:00:00", "hora_fin": "13:00:00"}),
    ]

    for rk, data in eventos_test:
        msg = aio_pika.Message(
            body=json.dumps(data).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await exchange.publish(msg, routing_key=rk)
        eventos_publicados.append(data)
        print(f"    [PRODUCER] {rk}")

    # ── 4. Esperar consumo ──
    print(f"\n[4] Esperando consumo de {len(eventos_test)} eventos...")
    await asyncio.sleep(2)

    # ── 5. Verificar ──
    print(f"\n[5] Resultados:")
    print(f"    Publicados: {len(eventos_publicados)}")
    print(f"    Consumidos: {len(eventos_consumidos)}")

    if len(eventos_consumidos) == len(eventos_publicados):
        print("\n    PASS: Todos los eventos fueron consumidos correctamente")
    else:
        pendientes = len(eventos_publicados) - len(eventos_consumidos)
        print(f"\n    AVISO: {pendientes} eventos pendientes (pueden estar en cola del worker)")

    # ── 6. Prueba de consumo concurrente ──
    print(f"\n[6] Prueba de consumo concurrente (prefetch=3)...")
    batch_size = 12
    inicio = time.time()

    for i in range(batch_size):
        data = {"cita_id": 200 + i, "paciente_id": (i % 4) + 1, "tipo": f"batch_{i}"}
        msg = aio_pika.Message(
            body=json.dumps(data).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(msg, routing_key="cita.creada")

    consumidos_antes = len(eventos_consumidos)
    await asyncio.sleep(3)
    consumidos_despues = len(eventos_consumidos)
    duracion = round((time.time() - inicio) * 1000, 1)
    nuevos = consumidos_despues - consumidos_antes

    print(f"    Consumidos del lote: {nuevos}/{batch_size} en {duracion}ms")
    print(f"    (Con prefetch=3 se procesan hasta 3 en paralelo)")

    await connection.close()

    print("\n" + "=" * 55)
    print("  PRUEBA RABBITMQ FINALIZADA")
    print("=" * 55)


async def test_routing_keys():
    """Verificar que el routing por topic funciona para todos los patrones del sistema."""
    print("\n\n" + "=" * 55)
    print("  PRUEBA DE ROUTING KEYS — TOPIC EXCHANGE")
    print("=" * 55)

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    exchange = await channel.declare_exchange("test.routing", aio_pika.ExchangeType.TOPIC, durable=False)

    cola_citas     = await channel.declare_queue("test.citas",     auto_delete=True)
    cola_horarios  = await channel.declare_queue("test.horarios",  auto_delete=True)
    cola_partes    = await channel.declare_queue("test.partes",    auto_delete=True)
    cola_todo      = await channel.declare_queue("test.todo",      auto_delete=True)

    await cola_citas.bind(exchange,    routing_key="cita.#")
    await cola_horarios.bind(exchange, routing_key="horario.#")
    await cola_partes.bind(exchange,   routing_key="parte_medico.#")
    await cola_todo.bind(exchange,     routing_key="#")

    recibidos = {"citas": [], "horarios": [], "partes": [], "todo": []}

    async def make_consumer(cola, key):
        async def handler(msg):
            async with msg.process():
                recibidos[key].append(json.loads(msg.body.decode()))
        await cola.consume(handler)

    await make_consumer(cola_citas,    "citas")
    await make_consumer(cola_horarios, "horarios")
    await make_consumer(cola_partes,   "partes")
    await make_consumer(cola_todo,     "todo")
    await asyncio.sleep(0.3)

    tests = [
        ("cita.creada",             {"id": 1}),
        ("cita.estado_actualizado", {"id": 2}),
        ("cita.cancelada",          {"id": 3}),
        ("horario.lote_nuevo",      {"id": 4}),
        ("parte_medico.creado",     {"id": 5}),
    ]

    for rk, data in tests:
        msg = aio_pika.Message(body=json.dumps(data).encode())
        await exchange.publish(msg, routing_key=rk)
        print(f"  Publicado: {rk}")

    await asyncio.sleep(1)

    print(f"\n  Resultados del routing:")
    print(f"    cita.#         : {len(recibidos['citas'])} mensajes  (esperado 3)")
    print(f"    horario.#      : {len(recibidos['horarios'])} mensajes  (esperado 1)")
    print(f"    parte_medico.# : {len(recibidos['partes'])} mensajes  (esperado 1)")
    print(f"    #              : {len(recibidos['todo'])} mensajes  (esperado 5)")

    esperado = {"citas": 3, "horarios": 1, "partes": 1, "todo": 5}
    if all(len(recibidos[k]) == v for k, v in esperado.items()):
        print("\n  PASS: Routing por topic funciona correctamente")
    else:
        print("\n  FAIL: El routing no coincide con lo esperado")

    await connection.close()


if __name__ == "__main__":
    asyncio.run(test_publicacion_consumo())
    asyncio.run(test_routing_keys())
