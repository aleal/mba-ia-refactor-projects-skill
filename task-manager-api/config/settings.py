import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool(name, default):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes')


def _list(name, default):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


class Settings:
    # Sem SECRET_KEY no ambiente, gera uma chave efêmera: tokens emitidos não sobrevivem a um restart.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    TOKEN_MAX_AGE = int(os.environ.get('TOKEN_MAX_AGE', '28800'))

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _bool('FLASK_DEBUG', 'false')
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    CORS_ORIGINS = _list('CORS_ORIGINS', 'http://localhost:3000')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    NOTIFICATIONS_ENABLED = _bool('NOTIFICATIONS_ENABLED', 'false')
    SMTP_HOST = os.environ.get('SMTP_HOST', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
