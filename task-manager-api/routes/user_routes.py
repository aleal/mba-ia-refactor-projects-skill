from flask import Blueprint

from middlewares.auth import current_user, require_auth
from models.constants import ADMIN_ROLE, DEFAULT_ROLE
from routes.responses import json_body, respond


def _requests_privileged_role():
    body = json_body()
    return isinstance(body, dict) and body.get('role', DEFAULT_ROLE) != DEFAULT_ROLE


def build_user_routes(user_controller, auth_controller):
    bp = Blueprint('users', __name__)

    @bp.get('/users')
    @require_auth(ADMIN_ROLE)
    def list_users():
        return respond(user_controller.list_users())

    @bp.get('/users/<int:user_id>')
    @require_auth(ADMIN_ROLE, self_param='user_id')
    def get_user(user_id):
        return respond(user_controller.get_user(user_id))

    @bp.post('/users')
    @require_auth(ADMIN_ROLE, when=_requests_privileged_role)  # signup público só com role 'user'
    def create_user():
        return respond(user_controller.create_user(json_body()))

    @bp.put('/users/<int:user_id>')
    @require_auth(ADMIN_ROLE, self_param='user_id')
    def update_user(user_id):
        return respond(user_controller.update_user(user_id, json_body(), current_user()))

    @bp.delete('/users/<int:user_id>')
    @require_auth(ADMIN_ROLE)
    def delete_user(user_id):
        return respond(user_controller.delete_user(user_id))

    @bp.get('/users/<int:user_id>/tasks')
    def list_user_tasks(user_id):
        return respond(user_controller.list_user_tasks(user_id))

    @bp.post('/login')
    def login():
        return respond(auth_controller.login(json_body()))

    return bp
