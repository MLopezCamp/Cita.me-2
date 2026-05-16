"""
cita.me — Middleware para propagar request_id vía ContextVar
"""
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdMiddleware(BaseHTTPMiddleware):  # Heredar de BaseHTTPMiddleware
    async def dispatch(self, request: Request, call_next):
        # Recibir de header o generar uno nuevo (8 chars para legibilidad)
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request_id_var.set(rid)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


def get_request_id() -> str:
    return request_id_var.get()