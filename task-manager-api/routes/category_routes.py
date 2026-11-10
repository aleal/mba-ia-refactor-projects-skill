from flask import Blueprint

from middlewares.auth import require_auth
from models.constants import ADMIN_ROLE
from routes.responses import json_body, respond


def build_category_routes(controller):
    bp = Blueprint('categories', __name__)

    @bp.get('/categories')
    def list_categories():
        return respond(controller.list_categories())

    @bp.post('/categories')
    @require_auth(ADMIN_ROLE)
    def create_category():
        return respond(controller.create_category(json_body()))

    @bp.put('/categories/<int:cat_id>')
    @require_auth(ADMIN_ROLE)
    def update_category(cat_id):
        return respond(controller.update_category(cat_id, json_body()))

    @bp.delete('/categories/<int:cat_id>')
    @require_auth(ADMIN_ROLE)
    def delete_category(cat_id):
        return respond(controller.delete_category(cat_id))

    return bp
