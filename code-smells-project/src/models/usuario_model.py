from werkzeug.security import check_password_hash, generate_password_hash

TIPO_PADRAO = "cliente"

# A senha nunca sai do model.
USUARIO_CAMPOS = ("id", "nome", "email", "tipo", "criado_em")
LOGIN_CAMPOS = ("id", "nome", "email", "tipo")


def usuario_to_dict(row, campos=USUARIO_CAMPOS):
    return {campo: row[campo] for campo in campos}


class UsuarioModel:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def listar(self):
        rows = self._get_connection().execute("SELECT * FROM usuarios").fetchall()
        return [usuario_to_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._get_connection().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return usuario_to_dict(row) if row else None

    def existe(self, usuario_id):
        row = self._get_connection().execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return row is not None

    def criar(self, nome, email, senha, tipo=TIPO_PADRAO):
        db = self._get_connection()
        with db:
            cursor = db.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, generate_password_hash(senha), tipo),
            )
        return cursor.lastrowid

    def autenticar(self, email, senha):
        rows = self._get_connection().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchall()
        for row in rows:
            if row["senha"] and check_password_hash(row["senha"], senha):
                return usuario_to_dict(row, LOGIN_CAMPOS)
        return None

    def contar(self):
        return self._get_connection().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
