import logging

from controllers.validators import validate_credentials
from middlewares.error_handler import ForbiddenError, UnauthorizedError
from models.user import User

logger = logging.getLogger(__name__)


class AuthController:
    def __init__(self, token_service):
        self._tokens = token_service

    def login(self, data):
        email, password = validate_credentials(data)
        user = User.get_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        if user.needs_rehash():
            user.set_password(password)
            user.save()
            logger.info('hash de senha legado migrado user_id=%s', user.id)
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self._tokens.issue(user),
        }, 200
