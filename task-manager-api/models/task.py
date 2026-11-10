from sqlalchemy.orm import joinedload

from database import db, PersistenceMixin
from models.constants import CLOSED_TASK_STATUSES, DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, HIGH_PRIORITY_MAX
from utils.dates import utcnow


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


class Task(PersistenceMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    # ---- regras da entidade ----

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_TASK_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    def apply(self, changes):
        for field, value in changes.items():
            setattr(self, field, value)
        self.updated_at = utcnow()

    # ---- serialização ----

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_dict_with_overdue(self):
        data = self.to_dict()
        data['overdue'] = self.is_overdue()
        return data

    def to_list_item(self):
        data = self.to_dict_with_overdue()
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_user_summary(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # ---- consultas ----

    @classmethod
    def get_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        query = db.select(cls).options(joinedload(cls.user), joinedload(cls.category)).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = db.select(cls).order_by(cls.id)
        if text:
            query = query.where(db.or_(cls.title.like(f'%{text}%'), cls.description.like(f'%{text}%')))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def count_all(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()

    @classmethod
    def count_by(cls, column):
        rows = db.session.execute(db.select(column, db.func.count(cls.id)).group_by(column)).all()
        return {value: total for value, total in rows}

    @classmethod
    def count_by_status(cls):
        return cls.count_by(cls.status)

    @classmethod
    def count_by_priority(cls):
        return cls.count_by(cls.priority)

    @classmethod
    def _overdue_filter(cls, now):
        return db.and_(cls.due_date.isnot(None), cls.due_date < now, cls.status.notin_(CLOSED_TASK_STATUSES))

    @classmethod
    def count_overdue(cls, now):
        return db.session.execute(db.select(db.func.count(cls.id)).where(cls._overdue_filter(now))).scalar_one()

    @classmethod
    def list_overdue(cls, now):
        query = db.select(cls).where(cls._overdue_filter(now)).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def count_created_since(cls, since):
        return db.session.execute(db.select(db.func.count(cls.id)).where(cls.created_at >= since)).scalar_one()

    @classmethod
    def count_done_since(cls, since):
        query = db.select(db.func.count(cls.id)).where(cls.status == 'done', cls.updated_at >= since)
        return db.session.execute(query).scalar_one()

    @staticmethod
    def summarize(tasks, now=None):
        """Estatísticas de uma lista de tasks (usado no relatório por usuário)."""
        now = now or utcnow()
        stats = {'total_tasks': len(tasks), 'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0,
                 'overdue': 0, 'high_priority': 0}
        for task in tasks:
            if task.status in stats:
                stats[task.status] += 1
            if task.priority <= HIGH_PRIORITY_MAX:
                stats['high_priority'] += 1
            if task.is_overdue(now):
                stats['overdue'] += 1
        stats['completion_rate'] = completion_rate(stats['done'], stats['total_tasks'])
        return stats
