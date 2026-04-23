import time
from .celery_worker import celery_app

@celery_app.task(bind=True, name="tasks.enviar_correo_confirmacion")
def enviar_correo_confirmacion(self, cita_id: int, email_paciente: str, medico_nombre: str, fecha: str, hora: str):
    """
    Simula el envio de un correo electronico de confirmacion de cita.
    En un entorno real, se integraria con un servicio de email (SMTP, SendGrid, etc.)
    """
    print(f"Procesando cita {cita_id} para {email_paciente}")
    time.sleep(3)
    mensaje = f"""
    Confirmacion de cita medica:
    Medico: {medico_nombre}
    Fecha: {fecha} a las {hora}
    Gracias por confiar en nosotros.
    """
    print(mensaje)
    return {"cita_id": cita_id, "enviado": True}