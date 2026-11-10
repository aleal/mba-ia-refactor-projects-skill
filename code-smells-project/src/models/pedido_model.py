from src.errors import ValidationError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

PRODUTO_DESCONHECIDO = "Desconhecido"

_PEDIDOS_COM_ITENS_SQL = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0


def _agrupar_pedidos(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or PRODUTO_DESCONHECIDO,
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


class PedidoModel:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def criar(self, usuario_id, itens):
        """Cria pedido, itens e baixa de estoque numa única transação."""
        db = self._get_connection()
        ids = sorted({item["produto_id"] for item in itens})
        placeholders = ", ".join("?" for _ in ids)  # apenas "?": os ids vão como parâmetros
        rows = db.execute(f"SELECT id, nome, preco, estoque FROM produtos WHERE id IN ({placeholders})", ids)
        produtos = {row["id"]: row for row in rows}

        total = 0
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado", sucesso=False)
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)
            total = total + (produto["preco"] * item["quantidade"])

        with db:  # commit no fim; rollback se qualquer passo falhar
            cursor = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid
            for item in itens:
                produto = produtos[item["produto_id"]]
                db.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
                )
                baixa = db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                )
                if baixa.rowcount == 0:
                    raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)

        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self):
        rows = self._get_connection().execute(_PEDIDOS_COM_ITENS_SQL + " ORDER BY p.id, i.id").fetchall()
        return _agrupar_pedidos(rows)

    def listar_por_usuario(self, usuario_id):
        rows = self._get_connection().execute(
            _PEDIDOS_COM_ITENS_SQL + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
        ).fetchall()
        return _agrupar_pedidos(rows)

    def atualizar_status(self, pedido_id, novo_status):
        db = self._get_connection()
        with db:
            db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))

    def resumo_vendas(self):
        row = self._get_connection().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(status = ?), 0) AS pendentes,
                   COALESCE(SUM(status = ?), 0) AS aprovados,
                   COALESCE(SUM(status = ?), 0) AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        return dict(row)

    def contar(self):
        return self._get_connection().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
