from flask import Blueprint, request

from src.middlewares.auth import require_admin_token


def build_pedido_routes(controller):
    bp = Blueprint("pedidos", __name__)

    def criar_pedido():
        return controller.criar(request.get_json(silent=True))

    def listar_todos_pedidos():
        return controller.listar_todos()

    def listar_pedidos_usuario(usuario_id):
        return controller.listar_por_usuario(usuario_id)

    def atualizar_status_pedido(pedido_id):
        return controller.atualizar_status(pedido_id, request.get_json(silent=True))

    # Criar pedido é ação do cliente; listar pedidos e mudar status são privilegiados.
    bp.add_url_rule("/pedidos", view_func=criar_pedido, methods=["POST"])
    bp.add_url_rule("/pedidos", view_func=require_admin_token(listar_todos_pedidos), methods=["GET"])
    bp.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>", view_func=require_admin_token(listar_pedidos_usuario), methods=["GET"]
    )
    bp.add_url_rule(
        "/pedidos/<int:pedido_id>/status", view_func=require_admin_token(atualizar_status_pedido), methods=["PUT"]
    )
    return bp
