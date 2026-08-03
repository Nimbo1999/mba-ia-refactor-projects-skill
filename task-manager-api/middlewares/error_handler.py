"""Tratamento de erro centralizado da aplicação.

Padroniza o formato de erro da API e evita vazar stack traces/detalhes internos
em produção.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = {"error": error.description, "success": False}
        return jsonify(response), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        logger.exception("Erro não tratado ao processar requisição")
        response = {"error": "Erro interno do servidor", "success": False}
        return jsonify(response), 500
