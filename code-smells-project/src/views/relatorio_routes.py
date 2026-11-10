from flask import Blueprint

from src.middlewares.auth import require_admin_token


def build_relatorio_routes(controller):
    bp = Blueprint("relatorios", __name__)

    def relatorio_vendas():
        return controller.vendas()

    bp.add_url_rule("/relatorios/vendas", view_func=require_admin_token(relatorio_vendas), methods=["GET"])
    return bp
