import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database import db, PersistenceMixin
from models.constants import ADMIN_ROLE, DEFAULT_ROLE
from models.task import Task, completion_rate
from utils.dates import utcnow


def _is_legacy_md5(stored):
    return len(stored) == 32 and '$' not in stored


class User(PersistenceMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship('Task', back_populates='user', cascade='all, delete-orphan', order_by='Task.id')

    def to_dict(self):
        # A senha (hash) nunca sai do model.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if _is_legacy_md5(self.password):
            # Somente leitura de hashes MD5 legados; quem chama regrava com o hash novo (needs_rehash).
            legacy = hashlib.md5(raw_password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, raw_password)

    def needs_rehash(self):
        return _is_legacy_md5(self.password)

    def is_admin(self):
        return self.role == ADMIN_ROLE

    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def get_by_email(cls, email):
        return db.session.execute(db.select(cls).filter_by(email=email)).scalar_one_or_none()

    @classmethod
    def list_with_task_counts(cls):
        query = (db.select(cls, db.func.count(Task.id))
                 .outerjoin(Task, Task.user_id == cls.id)
                 .group_by(cls.id)
                 .order_by(cls.id))
        return db.session.execute(query).all()

    @classmethod
    def productivity(cls):
        done = db.func.sum(db.case((Task.status == 'done', 1), else_=0))
        query = (db.select(cls.id, cls.name, db.func.count(Task.id), db.func.coalesce(done, 0))
                 .outerjoin(Task, Task.user_id == cls.id)
                 .group_by(cls.id)
                 .order_by(cls.id))
        return [
            {
                'user_id': user_id,
                'user_name': name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': completion_rate(completed, total),
            }
            for user_id, name, total, completed in db.session.execute(query).all()
        ]

    @classmethod
    def count_all(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()
