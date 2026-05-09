"""
Contexto de trazabilidad por peticion.

ContextVar permite que el request_id viaje automaticamente
por todo el codigo async sin pasarlo como parametro.
Cada tarea asyncio tiene su propia copia del valor.
"""
import uuid
from contextvars import ContextVar

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id_var.get()


def set_request_id(rid: str) -> None:
    _request_id_var.set(rid)


def new_request_id() -> str:
    """Genera un ID corto y lo almacena en el contexto actual."""
    rid = str(uuid.uuid4())[:8]
    _request_id_var.set(rid)
    return rid
