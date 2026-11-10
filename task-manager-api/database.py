from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class PersistenceMixin:
    """Persistência atômica: cada save/delete é uma transação, com rollback em caso de falha."""

    def save(self):
        db.session.add(self)
        _commit()
        return self

    def delete(self):
        db.session.delete(self)
        _commit()


def _commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
