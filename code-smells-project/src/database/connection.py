import logging
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

PASSWORD_HASH_PREFIXES = ("scrypt:", "pbkdf2:")

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER REFERENCES usuarios(id),
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # produto_id fica sem FK de propósito: o item guarda preco_unitario e sobrevive
    # à exclusão do produto (a listagem mostra "Desconhecido"), como na API original.
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

SEED_PRODUTOS = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

# Contas de demonstração (clientes sem privilégio). A senha do admin vem da config.
SEED_CLIENTES = (
    ("João Silva", "joao@email.com", "123456"),
    ("Maria Santos", "maria@email.com", "senha123"),
)


def _connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """Conexão da requisição atual (uma por app context, fechada no teardown)."""
    if "db" not in g:
        g.db = _connect(current_app.config["DATABASE_PATH"])
    return g.db


def get_readonly_db():
    """Conexão que o SQLite impede de escrever, usada pela consulta administrativa."""
    if "readonly_db" not in g:
        conn = _connect(current_app.config["DATABASE_PATH"])
        conn.execute("PRAGMA query_only = ON")
        g.readonly_db = conn
    return g.readonly_db


def close_db(_exc=None):
    for key in ("db", "readonly_db"):
        conn = g.pop(key, None)
        if conn is not None:
            conn.close()


def _create_schema(conn):
    with conn:
        for ddl in SCHEMA:
            conn.execute(ddl)


def _seed(conn, admin_password):
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    usuarios = [("Admin", "admin@loja.com", generate_password_hash(admin_password), "admin")]
    usuarios += [(nome, email, generate_password_hash(senha), "cliente") for nome, email, senha in SEED_CLIENTES]
    with conn:
        conn.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            SEED_PRODUTOS,
        )
        conn.executemany("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", usuarios)
    logger.info("banco populado com dados de exemplo")


def _migrate_plaintext_passwords(conn):
    """Bancos criados pela versão antiga guardam senha em texto puro: regrava com hash."""
    rows = conn.execute("SELECT id, senha FROM usuarios").fetchall()
    legacy = [row for row in rows if row["senha"] and not row["senha"].startswith(PASSWORD_HASH_PREFIXES)]
    if not legacy:
        return
    with conn:
        conn.executemany(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            [(generate_password_hash(row["senha"]), row["id"]) for row in legacy],
        )
    logger.warning("%d senha(s) em texto puro migrada(s) para hash", len(legacy))


def init_db(app, admin_password):
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = get_db()
        _create_schema(conn)
        _seed(conn, admin_password)
        _migrate_plaintext_passwords(conn)
