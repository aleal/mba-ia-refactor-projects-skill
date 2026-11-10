import logging
import sqlite3

logger = logging.getLogger(__name__)


class SistemaController:
    def __init__(self, produto_model, usuario_model, pedido_model, versao, ambiente):
        self.produtos = produto_model
        self.usuarios = usuario_model
        self.pedidos = pedido_model
        self.versao = versao
        self.ambiente = ambiente

    def index(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self.versao,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }, 200

    def health(self):
        try:
            counts = {
                "produtos": self.produtos.contar(),
                "usuarios": self.usuarios.contar(),
                "pedidos": self.pedidos.contar(),
            }
        except sqlite3.Error:
            logger.exception("health check: falha ao acessar o banco")
            return {"status": "erro", "detalhes": "Falha ao acessar o banco de dados"}, 500
        # Sem secret_key, db_path ou debug: configuração interna não sai na resposta.
        return {
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": self.versao,
            "ambiente": self.ambiente,
        }, 200
