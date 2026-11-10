import hmac
from functools import wraps

from flask import current_app, request

from src.errors import UnauthorizedError

ADMIN_TOKEN_HEADER = "X-Admin-Token"


def require_admin_token(view):
    """Exige o token de serviço da config. Sem ADMIN_TOKEN configurado, nega sempre (fail-closed)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        provided = request.headers.get(ADMIN_TOKEN_HEADER, "")
        if not expected or not hmac.compare_digest(provided.encode(), expected.encode()):
            raise UnauthorizedError("Credencial administrativa ausente ou inválida", sucesso=False)
        return view(*args, **kwargs)

    return wrapper
