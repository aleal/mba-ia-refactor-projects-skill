from flask import Blueprint, request

from routes.responses import json_body, respond


def build_task_routes(controller):
    bp = Blueprint('tasks', __name__)

    @bp.get('/tasks')
    def list_tasks():
        return respond(controller.list_tasks())

    @bp.get('/tasks/<int:task_id>')
    def get_task(task_id):
        return respond(controller.get_task(task_id))

    @bp.post('/tasks')
    def create_task():
        return respond(controller.create_task(json_body()))

    @bp.put('/tasks/<int:task_id>')
    def update_task(task_id):
        return respond(controller.update_task(task_id, json_body()))

    @bp.delete('/tasks/<int:task_id>')
    def delete_task(task_id):
        return respond(controller.delete_task(task_id))

    @bp.get('/tasks/search')
    def search_tasks():
        return respond(controller.search_tasks(request.args))

    @bp.get('/tasks/stats')
    def task_stats():
        return respond(controller.stats())

    return bp
