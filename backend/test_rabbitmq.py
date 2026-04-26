"""
PRUEBA DE COMUNICACIÓN ASÍNCRONA — RabbitMQ
============================================

Ejecutar con RabbitMQ corriendo:
    python test_rabbitmq.py

Demuestra:
- Publicación de eventos a un exchange topic
- Consumo concurrente con prefetch_count
- Comunicación entre procesos (producer → consumer)
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
    """Publicar eventos y verificar que se consumen correctamente."""
    print("=" * 50)
    print("  PRUEBA DE RABBITMQ — COMUNICACIÓN ASÍNRONA")
    print("=" * 50)

    eventos_publicados = []
    eventos_consumidos = []

    # ── 1. Conectar ──
    print("\n[1] Conectando a RabbitMQ...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    # Prefetch = 3: procesar hasta 3 mensajes concurrentemente
    await channel.set_qos(prefetch_count=3)

    # Declarar exchange y cola
    exchange = await channel.declare_exchange(EXCHANGE_CITAS, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(QUEUE_CITAS, durable=True)
    await queue.bind(exchange, routing_key="cita.#")
    print("    ✓ Conexión establecida, exchange y cola declarados")

    # ── 2. Consumidor ──
    print("\n[2] Iniciando consumer...")

    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = json.loads(message.body.decode())
            routing_key = message.routing_key
            eventos_consumidos.append(body)

            # Simular procesamiento async (notificación, estadísticas)
            await asyncio.sleep(0.1)
            print(f"    [CONSUMER] {routing_key}: {body.get('cita_id', 'N/A')} — {body.get('tipo', '')}")

    await queue.consume(on_message)
    await asyncio.sleep(0.5)  # Dar tiempo al consumer a registrarse
    print("    ✓ Consumer registrado con prefetch_count=3")

    # ── 3. Publicar eventos ──
    print("\n[3] Publicando eventos...")
    eventos_test = [
        {"routing_key": "cita.creada", "data": {"cita_id": 1, "tipo": "nueva_reserva", "paciente_id": 10}},
        {"routing_key": "cita.creada", "data": {"cita_id": 2, "tipo": "nueva_reserva", "paciente_id": 11}},
        {"routing_key": "cita.estado_actualizado", "data": {"cita_id": 1, "tipo": "confirmacion", "nuevo_estado": "confirmada"}},
        {"routing_key": "cita.creada", "data": {"cita_id": 3, "tipo": "nueva_reserva", "paciente_id": 12}},
        {"routing_key": "cita.cancelada", "data": {"cita_id": 2, "tipo": "cancelacion", "motivo": "paciente_no_asistio"}},
        {"routing_key": "cita.estado_actualizado", "data": {"cita_id": 3, "tipo": "completada", "nuevo_estado": "completada"}},
    ]

    for evt in eventos_test:
        message = aio_pika.Message(
            body=json.dumps(evt["data"]).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await exchange.publish(message, routing_key=evt["routing_key"])
        eventos_publicados.append(evt["data"])
        print(f"    [PRODUCER] {evt['routing_key']}: {evt['data'].get('cita_id', 'N/A')}")

    # ── 4. Esperar consumo ──
    print(f"\n[4] Esperando consumo de {len(eventos_test)} eventos...")
    await asyncio.sleep(2)  # Tiempo para que el consumer procese

    # ── 5. Verificar ──
    print(f"\n[5] Resultados:")
    print(f"    Eventos publicados: {len(eventos_publicados)}")
    print(f"    Eventos consumidos: {len(eventos_consumidos)}")

    if len(eventos_consumidos) == len(eventos_publicados):
        print("\n    ✓ PASS: Todos los eventos fueron consumidos correctamente")
        print("    ✓ Comunicación async funcionando entre producer y consumer")
    else:
        print(f"\n    ⚠ {len(eventos_publicados) - len(eventos_consumidos)} eventos no fueron consumidos")
        print("    (Puede requerir más tiempo de espera)")

    # ── 6. Prueba de concurrencia de consumo ──
    print(f"\n[6] Prueba de consumo concurrente (prefetch=3)...")
    batch_size = 10
    print(f"    Publicando lote de {batch_size} eventos...")

    inicio = time.time()
    for i in range(batch_size):
        data = {"cita_id": 100 + i, "tipo": f"batch_test_{i}"}
        message = aio_pika.Message(
            body=json.dumps(data).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key="cita.creada")

    consumidos_antes = len(eventos_consumidos)
    await asyncio.sleep(3)
    consumidos_despues = len(eventos_consumidos)

    duracion = round((time.time() - inicio) * 1000, 1)
    nuevos = consumidos_despues - consumidos_antes
    print(f"    Consumidos en lote: {nuevos}/{batch_size} en {duracion}ms")
    print(f"    (Con prefetch=3, se procesan hasta 3 en paralelo)")

    # ── Cleanup ──
    await connection.close()

    print("\n" + "=" * 50)
    print("  PRUEBA RABBITMQ FINALIZADA")
    print("=" * 50)


async def test_routing_keys():
    """Probar que el routing por topic funciona correctamente."""
    print("\n\n" + "=" * 50)
    print("  PRUEBA DE ROUTING KEYS — TOPIC EXCHANGE")
    print("=" * 50)

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    exchange = await channel.declare_exchange("test.exchange", aio_pika.ExchangeType.TOPIC, durable=False)

    # Crear colas con diferentes routing patterns
    cola_todos = await channel.declare_queue("test.todos", auto_delete=True)
    cola_creadas = await channel.declare_queue("test.creadas", auto_delete=True)
    cola_canceladas = await channel.declare_queue("test.canceladas", auto_delete=True)

    await cola_todos.bind(exchange, routing_key="cita.#")
    await cola_creadas.bind(exchange, routing_key="cita.creada")
    await cola_canceladas.bind(exchange, routing_key="cita.cancelada")

    recibidos = {"todos": [], "creadas": [], "canceladas": []}

    async def make_consumer(cola, key):
        async def handler(msg):
            async with msg.process():
                recibidos[key].append(json.loads(msg.body.decode()))
        await cola.consume(handler)

    await make_consumer(cola_todos, "todos")
    await make_consumer(cola_creadas, "creadas")
    await make_consumer(cola_canceladas, "canceladas")
    await asyncio.sleep(0.3)

    # Publicar eventos con diferentes routing keys
    tests = [
        ("cita.creada", {"id": 1}),
        ("cita.cancelada", {"id": 2}),
        ("cita.estado_actualizado", {"id": 3}),
        ("cita.creada", {"id": 4}),
    ]

    for rk, data in tests:
        msg = aio_pika.Message(body=json.dumps(data).encode())
        await exchange.publish(msg, routing_key=rk)
        print(f"  Publicado: {rk}")

    await asyncio.sleep(1)

    print(f"\n  Resultados del routing:")
    print(f"    test.todos (cita.#):        {len(recibidos['todos'])} mensajes → {recibidos['todos']}")
    print(f"    test.creadas (cita.creada): {len(recibidos['creadas'])} mensajes → {recibidos['creadas']}")
    print(f"    test.canceladas (cita.cancelada): {len(recibidos['canceladas'])} mensajes → {recibidos['canceladas']}")

    expected = {"todos": 4, "creadas": 2, "canceladas": 1}
    if all(len(recibidos[k]) == v for k, v in expected.items()):
        print("\n  ✓ PASS: Routing por topic funciona correctamente")
    else:
        print("\n  ✗ FAIL: El routing no coincide con lo esperado")

    await connection.close()


if __name__ == "__main__":
    asyncio.run(test_publicacion_consumo())
    asyncio.run(test_routing_keys())