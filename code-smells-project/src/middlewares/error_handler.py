import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({"erro": err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
