from flask import Blueprint

from utils.dates import utcnow


def build_system_routes():
    bp = Blueprint('system', __name__)

    @bp.get('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(utcnow())}

    @bp.get('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return bp
