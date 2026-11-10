import logging
import sqlite3

from src.errors import ForbiddenError, ValidationError

logger = logging.getLogger(__name__)


class AdminController:
    def __init__(self, admin_model, query_enabled, reset_enabled):
        self.admin = admin_model
        self.query_enabled = query_enabled
        self.reset_enabled = reset_enabled

    def resetar_banco(self):
        if not self.reset_enabled:
            raise ForbiddenError("Endpoint desabilitado", sucesso=False)
        self.admin.resetar()
        logger.warning("banco de dados resetado via /admin/reset-db")
        return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200

    def executar_query(self, dados):
        if not self.query_enabled:
            raise ForbiddenError("Endpoint desabilitado", sucesso=False)
        dados = dados if isinstance(dados, dict) else {}
        sql = dados.get("sql", "")
        if not sql or not isinstance(sql, str):
            raise ValidationError("Query não informada")
        if not sql.lstrip().upper().startswith("SELECT"):
            raise ValidationError("Apenas consultas SELECT são permitidas")
        try:
            resultado = self.admin.consultar(sql)
        except sqlite3.Error:
            logger.warning("consulta administrativa rejeitada pelo banco", exc_info=True)
            raise ValidationError("Query inválida")
        return {"dados": resultado, "sucesso": True}, 200
