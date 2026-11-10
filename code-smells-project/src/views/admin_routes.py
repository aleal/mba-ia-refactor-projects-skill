from flask import Blueprint, request

from src.middlewares.auth import require_admin_token


def build_admin_routes(controller):
    bp = Blueprint("admin", __name__)

    def reset_database():
        return controller.resetar_banco()

    def executar_query():
        return controller.executar_query(request.get_json(silent=True))

    # Além do token, as duas operações ficam desligadas por padrão (ENABLE_ADMIN_RESET / ENABLE_ADMIN_QUERY).
    bp.add_url_rule("/admin/reset-db", view_func=require_admin_token(reset_database), methods=["POST"])
    bp.add_url_rule("/admin/query", view_func=require_admin_token(executar_query), methods=["POST"])
    return bp
