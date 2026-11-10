import logging

from controllers.validators import validate_new_user, validate_role, validate_user_changes
from middlewares.error_handler import ConflictError, ForbiddenError, NotFoundError
from models.user import User

logger = logging.getLogger(__name__)


class UserController:
    def list_users(self):
        result = []
        for user, task_count in User.list_with_task_counts():
            data = user.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result, 200

    def get_user(self, user_id):
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in user.tasks]
        return data, 200

    def create_user(self, data):
        fields = validate_new_user(data)
        if User.get_by_email(fields['email']):
            raise ConflictError('Email já cadastrado')
        validate_role(fields['role'])
        user = User(name=fields['name'], email=fields['email'], role=fields['role'])
        user.set_password(fields['password'])
        user.save()
        logger.info('usuário criado id=%s', user.id)
        return user.to_dict(), 201

    def update_user(self, user_id, data, actor):
        user = self._get_or_404(user_id)
        changes = validate_user_changes(data)
        if ('role' in changes or 'active' in changes) and not actor.is_admin():
            raise ForbiddenError('Permissão insuficiente')
        if 'email' in changes:
            existing = User.get_by_email(changes['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
        password = changes.pop('password', None)
        for field, value in changes.items():
            setattr(user, field, value)
        if password is not None:
            user.set_password(password)
        user.save()
        return user.to_dict(), 200

    def delete_user(self, user_id):
        # As tasks do usuário são removidas pelo cascade do relacionamento, na mesma transação.
        self._get_or_404(user_id).delete()
        logger.info('usuário deletado id=%s', user_id)
        return {'message': 'Usuário deletado com sucesso'}, 200

    def list_user_tasks(self, user_id):
        user = self._get_or_404(user_id)
        return [task.to_user_summary() for task in user.tasks], 200

    @staticmethod
    def _get_or_404(user_id):
        user = User.get_by_id(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return user
