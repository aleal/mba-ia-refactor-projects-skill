CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_MIN_LEN = 2
NOME_MAX_LEN = 200

PRODUTO_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def produto_to_dict(row):
    return {campo: row[campo] for campo in PRODUTO_CAMPOS}


class ProdutoModel:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def listar(self):
        rows = self._get_connection().execute("SELECT * FROM produtos").fetchall()
        return [produto_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._get_connection().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return produto_to_dict(row) if row else None

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        clauses, params = ["1=1"], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max:
            clauses.append("preco <= ?")
            params.append(preco_max)
        # Só cláusulas fixas entram no SQL; os valores vão como parâmetros.
        sql = "SELECT * FROM produtos WHERE " + " AND ".join(clauses)
        rows = self._get_connection().execute(sql, params).fetchall()
        return [produto_to_dict(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        db = self._get_connection()
        with db:
            cursor = db.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        db = self._get_connection()
        with db:
            db.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        db = self._get_connection()
        with db:
            db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self):
        return self._get_connection().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
