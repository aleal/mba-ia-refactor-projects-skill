from flask import Blueprint, request

from src.middlewares.auth import require_admin_token


def build_usuario_routes(controller):
    bp = Blueprint("usuarios", __name__)

    def listar_usuarios():
        return controller.listar()

    def buscar_usuario(usuario_id):
        return controller.buscar_por_id(usuario_id)

    def criar_usuario():
        return controller.criar(request.get_json(silent=True))

    def login():
        return controller.login(request.get_json(silent=True))

    # Cadastro e login são públicos; dados pessoais de terceiros são privilegiados.
    bp.add_url_rule("/usuarios", view_func=require_admin_token(listar_usuarios), methods=["GET"])
    bp.add_url_rule("/usuarios/<int:usuario_id>", view_func=require_admin_token(buscar_usuario), methods=["GET"])
    bp.add_url_rule("/usuarios", view_func=criar_usuario, methods=["POST"])
    bp.add_url_rule("/login", view_func=login, methods=["POST"])
    return bp
