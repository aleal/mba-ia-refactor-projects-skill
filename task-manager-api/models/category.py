from database import db, PersistenceMixin
from models.constants import DEFAULT_CATEGORY_COLOR
from models.task import Task
from utils.dates import utcnow


class Category(PersistenceMixin, db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_CATEGORY_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Sem cascade de delete: ao apagar a categoria, o ORM desassocia as tasks (category_id = NULL).
    tasks = db.relationship('Task', back_populates='category')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @classmethod
    def get_by_id(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_with_task_counts(cls):
        query = (db.select(cls, db.func.count(Task.id))
                 .outerjoin(Task, Task.category_id == cls.id)
                 .group_by(cls.id)
                 .order_by(cls.id))
        return db.session.execute(query).all()

    @classmethod
    def count_all(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()
