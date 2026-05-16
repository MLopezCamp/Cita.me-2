"""
cita.me — Configuración de logs en formato JSON para Loki.
"""
import json
import logging
import sys


class JSONFormatter(logging.Formatter):
    """Formatter que emite un JSON por línea para Loki."""

    def format(self, record):
        # ✅ Extraer request_id del ContextVar si no está en el record
        from middleware.request_id import get_request_id
        
        request_id = getattr(record, "request_id", None)
        if request_id == "-" or request_id is None:
            request_id = get_request_id()
        
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": getattr(record, "service", record.name),
            "request_id": request_id,
            "message": record.getMessage(),
        }
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """Configurar el root logger con formato JSON."""
    root = logging.getLogger()
    root.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root.setLevel(logging.INFO)
    root.addHandler(handler)

    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)