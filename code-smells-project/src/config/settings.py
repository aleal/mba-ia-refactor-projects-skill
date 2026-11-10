import os
import secrets


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


class Settings:
    """Configuração lida de variáveis de ambiente, com defaults seguros para desenvolvimento."""

    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = _env_bool("FLASK_DEBUG")
        self.HOST = os.environ.get("HOST", "127.0.0.1")
        self.PORT = int(os.environ.get("PORT", "5000"))
        self.DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = _env_list("CORS_ORIGINS")
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

        # Rotas privilegiadas exigem este token no header X-Admin-Token; vazio = sempre bloqueadas.
        self.ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
        # Operações perigosas ficam desligadas mesmo com token, até serem habilitadas explicitamente.
        self.ENABLE_ADMIN_QUERY = _env_bool("ENABLE_ADMIN_QUERY")
        self.ENABLE_ADMIN_RESET = _env_bool("ENABLE_ADMIN_RESET")

        # Senha do usuário admin criado pelo seed; sem a variável, é gerada aleatoriamente.
        self.SEED_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(16)

        self.APP_VERSION = "1.0.0"
        self.APP_ENV = os.environ.get("APP_ENV", "producao")
