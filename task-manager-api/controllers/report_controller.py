from datetime import timedelta

from middlewares.error_handler import NotFoundError
from models.category import Category
from models.constants import PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from models.task import Task
from models.user import User
from utils.dates import utcnow


class ReportController:
    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = Task.count_by_status()
        by_priority = Task.count_by_priority()
        overdue = Task.list_overdue(now)
        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': Task.count_all(),
                'total_users': User.count_all(),
                'total_categories': Category.count_all(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue),
                'tasks': [
                    {'id': task.id, 'title': task.title, 'due_date': str(task.due_date),
                     'days_overdue': (now - task.due_date).days}
                    for task in overdue
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': Task.count_created_since(since),
                'tasks_completed_last_7_days': Task.count_done_since(since),
            },
            'user_productivity': User.productivity(),
        }, 200

    def user_report(self, user_id):
        user = User.get_by_id(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': Task.summarize(user.tasks),
        }, 200
