from .celery_app import celery_app
import time
import asyncio
from app.models.database import SessionLocal
from app.models import crud
import smtplib
from email.message import EmailMessage

@celery_app.task(bind=True, max_retries=3)
def enviar_confirmacion_cita(self, cita_id: int, email_paciente: str, nombre_paciente: str, fecha_str: str):
    try:
        time.sleep(5)
        msg = EmailMessage()
        msg["Subject"] = "Confirmación de cita médica"
        msg["From"] = "noreply@citamedica.com"
        msg["To"] = email_paciente
        msg.set_content(f"Hola {nombre_paciente}, tu cita ha sido confirmada para {fecha_str}.")
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login("tu_email@gmail.com", "tu_contraseña")
            s.send_message(msg)
        return f"Correo enviado para cita {cita_id}"
    except Exception as e:
        raise self.retry(exc=e, countdown=60)

@celery_app.task
def liberar_lock_cita(lock_key: str):
    import redis
    r = redis.Redis.from_url(settings.redis_url)
    r.delete(lock_key)
    return f"Lock {lock_key} liberado"