class AdminModel:
    def __init__(self, get_connection, get_readonly_connection):
        self._get_connection = get_connection
        self._get_readonly_connection = get_readonly_connection

    def resetar(self):
        db = self._get_connection()
        with db:  # filhos antes dos pais
            db.execute("DELETE FROM itens_pedido")
            db.execute("DELETE FROM pedidos")
            db.execute("DELETE FROM produtos")
            db.execute("DELETE FROM usuarios")

    def consultar(self, sql):
        """Executa uma consulta numa conexão com query_only: o SQLite recusa qualquer escrita."""
        rows = self._get_readonly_connection().execute(sql).fetchall()
        return [dict(row) for row in rows]
