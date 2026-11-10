from flask import Blueprint, request

from src.middlewares.auth import require_admin_token


def build_produto_routes(controller):
    bp = Blueprint("produtos", __name__)

    def listar_produtos():
        return controller.listar()

    def buscar_produtos():
        return controller.buscar(request.args)

    def buscar_produto(produto_id):
        return controller.buscar_por_id(produto_id)

    def criar_produto():
        return controller.criar(request.get_json(silent=True))

    def atualizar_produto(produto_id):
        return controller.atualizar(produto_id, request.get_json(silent=True))

    def deletar_produto(produto_id):
        return controller.deletar(produto_id)

    # Leitura do catálogo é pública; escrita é privilegiada.
    bp.add_url_rule("/produtos", view_func=listar_produtos, methods=["GET"])
    bp.add_url_rule("/produtos/busca", view_func=buscar_produtos, methods=["GET"])
    bp.add_url_rule("/produtos/<int:produto_id>", view_func=buscar_produto, methods=["GET"])
    bp.add_url_rule("/produtos", view_func=require_admin_token(criar_produto), methods=["POST"])
    bp.add_url_rule("/produtos/<int:produto_id>", view_func=require_admin_token(atualizar_produto), methods=["PUT"])
    bp.add_url_rule("/produtos/<int:produto_id>", view_func=require_admin_token(deletar_produto), methods=["DELETE"])
    return bp
