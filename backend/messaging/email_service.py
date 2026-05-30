"""
cita.me — Servicio de envio de emails via Resend.
"""
import logging
import resend
from config import RESEND_API_KEY, RESEND_FROM_EMAIL

logger = logging.getLogger("email_service")

DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _fecha_legible(fecha_str: str) -> str:
    try:
        from datetime import date
        f = date.fromisoformat(fecha_str)
        dia_nombre = DIAS_SEMANA[f.weekday()]
        return f"{dia_nombre} {f.day} de {MESES[f.month - 1]} de {f.year}"
    except Exception:
        return fecha_str


async def send_cita_creada(
    paciente_email: str,
    paciente_nombre: str,
    fecha: str,
    hora: str,
    especialidad: str,
    doctor_nombre: str,
    motivo: str,
) -> None:
    if not RESEND_API_KEY:
        logger.warning("[EMAIL] RESEND_API_KEY no configurado, email omitido")
        return

    resend.api_key = RESEND_API_KEY

    hora_fmt = hora[:5] if hora else hora
    fecha_fmt = _fecha_legible(fecha)

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9fafb;padding:24px;">
      <div style="background:#ffffff;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="color:#1f2937;margin-top:0;">Cita medica registrada</h2>
        <p style="color:#6b7280;">Estimado/a <strong>{paciente_nombre}</strong>,</p>
        <p style="color:#6b7280;">Su cita ha sido registrada exitosamente y esta pendiente de confirmacion.</p>

        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Fecha y hora</strong><br>
              <span style="color:#6b7280;">{fecha_fmt} a las {hora_fmt}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Especialidad</strong><br>
              <span style="color:#6b7280;">{especialidad}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Doctor</strong><br>
              <span style="color:#6b7280;">{doctor_nombre}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;">
              <strong style="color:#374151;">Motivo de consulta</strong><br>
              <span style="color:#6b7280;">{motivo}</span>
            </td>
          </tr>
        </table>

        <p style="color:#6b7280;">Le notificaremos cuando su cita sea confirmada por el medico.</p>

        <p style="color:#9ca3af;font-size:12px;margin-bottom:0;">
          Este es un mensaje automatico de cita.me. Por favor no responda a este correo.
        </p>
      </div>
    </div>
    """

    try:
        params: resend.Emails.SendParams = {
            "from": RESEND_FROM_EMAIL,
            "to": [paciente_email],
            "subject":f"Cita registrada — {especialidad}",
            "html": html,
        }
        resend.Emails.send(params)
        logger.info("[EMAIL] Confirmacion de cita registrada enviada a %s", paciente_email)
    except Exception as e:
        logger.error("[EMAIL] Error enviando confirmacion de cita a %s: %s", paciente_email, e)


LABELS_ESTADO = {
    "confirmada": ("Cita confirmada", "Su cita ha sido confirmada por el medico.", "#16a34a"),
    "cancelada": ("Cita cancelada", "Su cita ha sido cancelada.", "#dc2626"),
    "completada": ("Cita completada", "Su cita ha sido marcada como completada.", "#2563eb"),
}


async def send_cita_estado_actualizado(
    paciente_email: str,
    paciente_nombre: str,
    fecha: str,
    hora: str,
    especialidad: str,
    doctor_nombre: str,
    nuevo_estado: str,
) -> None:
    if not RESEND_API_KEY:
        logger.warning("[EMAIL] RESEND_API_KEY no configurado, email omitido")
        return

    if nuevo_estado not in LABELS_ESTADO:
        return

    resend.api_key = RESEND_API_KEY

    hora_fmt = hora[:5] if hora else hora
    fecha_fmt = _fecha_legible(fecha)
    asunto, mensaje, color = LABELS_ESTADO[nuevo_estado]

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9fafb;padding:24px;">
      <div style="background:#ffffff;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="color:{color};margin-top:0;">{asunto}</h2>
        <p style="color:#6b7280;">Estimado/a <strong>{paciente_nombre}</strong>,</p>
        <p style="color:#6b7280;">{mensaje}</p>

        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Fecha y hora</strong><br>
              <span style="color:#6b7280;">{fecha_fmt} a las {hora_fmt}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Especialidad</strong><br>
              <span style="color:#6b7280;">{especialidad}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;">
              <strong style="color:#374151;">Doctor</strong><br>
              <span style="color:#6b7280;">{doctor_nombre}</span>
            </td>
          </tr>
        </table>

        <p style="color:#9ca3af;font-size:12px;margin-bottom:0;">
          Este es un mensaje automatico de cita.me. Por favor no responda a este correo.
        </p>
      </div>
    </div>
    """

    try:
        params: resend.Emails.SendParams = {
            "from": RESEND_FROM_EMAIL,
            "to": [paciente_email],
            "subject":f"{asunto} — {especialidad}",
            "html": html,
        }
        resend.Emails.send(params)
        logger.info("[EMAIL] Notificacion de estado '%s' enviada a %s", nuevo_estado, paciente_email)
    except Exception as e:
        logger.error("[EMAIL] Error enviando notificacion de estado a %s: %s", paciente_email, e)


async def send_cita_completada(
    paciente_email: str,
    paciente_nombre: str,
    fecha: str,
    hora: str,
    especialidad: str,
    doctor_nombre: str,
    notas: str | None,
    diagnostico: str | None,
    tratamiento: str | None,
    observaciones: str | None,
) -> None:
    if not RESEND_API_KEY:
        logger.warning("[EMAIL] RESEND_API_KEY no configurado, email omitido")
        return

    resend.api_key = RESEND_API_KEY

    hora_fmt = hora[:5] if hora else hora
    fecha_fmt = _fecha_legible(fecha)

    secciones_parte = ""
    if diagnostico:
        secciones_parte += f"""
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
            <strong style="color:#374151;">Diagnostico</strong><br>
            <span style="color:#6b7280;">{diagnostico}</span>
          </td>
        </tr>"""
    if tratamiento:
        secciones_parte += f"""
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
            <strong style="color:#374151;">Tratamiento</strong><br>
            <span style="color:#6b7280;">{tratamiento}</span>
          </td>
        </tr>"""
    if observaciones:
        secciones_parte += f"""
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
            <strong style="color:#374151;">Observaciones</strong><br>
            <span style="color:#6b7280;">{observaciones}</span>
          </td>
        </tr>"""
    if notas:
        secciones_parte += f"""
        <tr>
          <td style="padding:8px 0;">
            <strong style="color:#374151;">Notas del doctor</strong><br>
            <span style="color:#6b7280;">{notas}</span>
          </td>
        </tr>"""

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9fafb;padding:24px;">
      <div style="background:#ffffff;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="color:#1f2937;margin-top:0;">Resumen de su cita medica</h2>
        <p style="color:#6b7280;">Estimado/a <strong>{paciente_nombre}</strong>,</p>
        <p style="color:#6b7280;">Su cita ha sido completada. A continuacion encontrara el resumen.</p>

        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Fecha</strong><br>
              <span style="color:#6b7280;">{fecha_fmt} a las {hora_fmt}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Especialidad</strong><br>
              <span style="color:#6b7280;">{especialidad}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Doctor</strong><br>
              <span style="color:#6b7280;">{doctor_nombre}</span>
            </td>
          </tr>
          {secciones_parte}
        </table>

        <p style="color:#9ca3af;font-size:12px;margin-bottom:0;">
          Este es un mensaje automatico de cita.me. Por favor no responda a este correo.
        </p>
      </div>
    </div>
    """

    try:
        params: resend.Emails.SendParams = {
            "from": RESEND_FROM_EMAIL,
            "to": [paciente_email],
            "subject":f"Resumen de su cita — {especialidad}",
            "html": html,
        }
        resend.Emails.send(params)
        logger.info("[EMAIL] Resumen de cita enviado a %s", paciente_email)
    except Exception as e:
        logger.error("[EMAIL] Error enviando resumen de cita a %s: %s", paciente_email, e)


async def send_nuevos_horarios(
    paciente_email: str,
    paciente_nombre: str,
    especialidad: str,
    doctor_nombre: str,
    dia_semana: int,
    hora_inicio: str,
    hora_fin: str,
) -> None:
    if not RESEND_API_KEY:
        logger.warning("[EMAIL] RESEND_API_KEY no configurado, email omitido")
        return

    resend.api_key = RESEND_API_KEY

    dia_nombre = DIAS_SEMANA[dia_semana] if 0 <= dia_semana <= 6 else str(dia_semana)
    hora_inicio_fmt = hora_inicio[:5] if hora_inicio else hora_inicio
    hora_fin_fmt = hora_fin[:5] if hora_fin else hora_fin

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f9fafb;padding:24px;">
      <div style="background:#ffffff;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="color:#1f2937;margin-top:0;">Nuevos horarios disponibles en {especialidad}</h2>
        <p style="color:#6b7280;">Estimado/a <strong>{paciente_nombre}</strong>,</p>
        <p style="color:#6b7280;">
          Se han habilitado nuevos horarios de atencion en <strong>{especialidad}</strong>
          que podrian ser de su interes.
        </p>

        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Doctor</strong><br>
              <span style="color:#6b7280;">{doctor_nombre}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #e5e7eb;">
              <strong style="color:#374151;">Especialidad</strong><br>
              <span style="color:#6b7280;">{especialidad}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;">
              <strong style="color:#374151;">Nuevo horario disponible</strong><br>
              <span style="color:#6b7280;">{dia_nombre} de {hora_inicio_fmt} a {hora_fin_fmt}</span>
            </td>
          </tr>
        </table>

        <p style="color:#6b7280;">
          Si desea reagendar su cita o reservar un nuevo turno, ingrese a la plataforma.
        </p>

        <p style="color:#9ca3af;font-size:12px;margin-bottom:0;">
          Este es un mensaje automatico de cita.me. Por favor no responda a este correo.
        </p>
      </div>
    </div>
    """

    try:
        params: resend.Emails.SendParams = {
            "from": RESEND_FROM_EMAIL,
            "to": [paciente_email],
            "subject":f"Nuevos horarios disponibles — {especialidad}",
            "html": html,
        }
        resend.Emails.send(params)
        logger.info("[EMAIL] Notificacion de nuevos horarios enviada a %s", paciente_email)
    except Exception as e:
        logger.error("[EMAIL] Error enviando notificacion de horarios a %s: %s", paciente_email, e)
