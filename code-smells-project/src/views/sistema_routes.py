from flask import Blueprint


def build_sistema_routes(controller):
    bp = Blueprint("sistema", __name__)

    def index():
        return controller.index()

    def health_check():
        return controller.health()

    bp.add_url_rule("/", view_func=index, methods=["GET"])
    bp.add_url_rule("/health", view_func=health_check, methods=["GET"])
    return bp
