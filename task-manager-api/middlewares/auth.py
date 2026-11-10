from functools import wraps

from flask import current_app, g, request

from middlewares.error_handler import ForbiddenError, UnauthorizedError
from models.user import User

BEARER_PREFIX = 'Bearer '


def _authenticate():
    header = request.headers.get('Authorization', '')
    if not header.startswith(BEARER_PREFIX):
        raise UnauthorizedError('Token inválido ou ausente')
    user_id = current_app.extensions['token_service'].verify(header[len(BEARER_PREFIX):])
    user = User.get_by_id(user_id) if user_id is not None else None
    if user is None or not user.active:
        raise UnauthorizedError('Token inválido ou ausente')
    g.current_user = user
    return user


def require_auth(*roles, self_param=None, when=None):
    """Exige `Authorization: Bearer <token>` válido.

    roles: papéis aceitos (vazio = qualquer usuário autenticado).
    self_param: nome do parâmetro da rota com o id do usuário; o próprio usuário também passa.
    when: predicado sobre o request; se devolver False, a rota segue sem exigir credencial.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if when is not None and not when():
                return view(*args, **kwargs)
            user = _authenticate()
            is_self = self_param is not None and kwargs.get(self_param) == user.id
            if roles and user.role not in roles and not is_self:
                raise ForbiddenError('Permissão insuficiente')
            return view(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    return g.get('current_user')
