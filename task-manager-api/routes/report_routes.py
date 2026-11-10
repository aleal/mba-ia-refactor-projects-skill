from flask import Blueprint

from middlewares.auth import require_auth
from models.constants import ADMIN_ROLE
from routes.responses import respond


def build_report_routes(controller):
    bp = Blueprint('reports', __name__)

    @bp.get('/reports/summary')
    @require_auth(ADMIN_ROLE)
    def summary_report():
        return respond(controller.summary())

    @bp.get('/reports/user/<int:user_id>')
    @require_auth(ADMIN_ROLE, self_param='user_id')
    def user_report(user_id):
        return respond(controller.user_report(user_id))

    return bp
