import logging

from controllers.validators import parse_int, validate_new_task, validate_task_changes
from middlewares.error_handler import NotFoundError
from models.category import Category
from models.task import Task, completion_rate
from models.user import User
from utils.dates import utcnow

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, notifier):
        self._notifier = notifier

    def list_tasks(self):
        return [task.to_list_item() for task in Task.list_with_relations()], 200

    def get_task(self, task_id):
        return self._get_or_404(task_id).to_dict_with_overdue(), 200

    def create_task(self, data):
        fields = validate_new_task(data)
        assignee = self._check_references(fields)
        task = Task(**fields).save()
        logger.info('task criada id=%s', task.id)
        if assignee:
            self._notifier.notify_task_assigned(assignee, task)
        return task.to_dict(), 201

    def update_task(self, task_id, data):
        task = self._get_or_404(task_id)
        changes = validate_task_changes(data)
        assignee = self._check_references(changes)
        previous_user_id = task.user_id
        task.apply(changes)
        task.save()
        logger.info('task atualizada id=%s', task.id)
        if assignee and assignee.id != previous_user_id:
            self._notifier.notify_task_assigned(assignee, task)
        return task.to_dict(), 200

    def delete_task(self, task_id):
        self._get_or_404(task_id).delete()
        logger.info('task deletada id=%s', task_id)
        return {'message': 'Task deletada com sucesso'}, 200

    def search_tasks(self, args):
        tasks = Task.search(
            text=args.get('q', ''),
            status=args.get('status', ''),
            priority=parse_int(args.get('priority'), 'Prioridade inválida'),
            user_id=parse_int(args.get('user_id'), 'Usuário inválido'),
        )
        return [task.to_dict() for task in tasks], 200

    def stats(self):
        total = Task.count_all()
        by_status = Task.count_by_status()
        done = by_status.get('done', 0)
        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': done,
            'cancelled': by_status.get('cancelled', 0),
            'overdue': Task.count_overdue(utcnow()),
            'completion_rate': completion_rate(done, total),
        }, 200

    @staticmethod
    def _get_or_404(task_id):
        task = Task.get_by_id(task_id)
        if task is None:
            raise NotFoundError('Task não encontrada')
        return task

    @staticmethod
    def _check_references(fields):
        """Garante que user_id/category_id informados existem; devolve o usuário atribuído (ou None)."""
        assignee = None
        if fields.get('user_id'):
            assignee = User.get_by_id(fields['user_id'])
            if assignee is None:
                raise NotFoundError('Usuário não encontrado')
        if fields.get('category_id') and Category.get_by_id(fields['category_id']) is None:
            raise NotFoundError('Categoria não encontrada')
        return assignee
