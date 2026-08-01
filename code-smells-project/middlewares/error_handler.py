"""Tratamento de erro centralizado.

Os controllers já tratam suas próprias exceções esperadas; este handler é a
rede de segurança para qualquer exceção não capturada, garantindo um formato
de resposta consistente e sem vazamento de stack-trace/detalhes internos.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def registrar(app):
    @app.errorhandler(404)
    def nao_encontrado(_error):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def erro_nao_tratado(error):
        if isinstance(error, HTTPException):
            # Preserva o comportamento padrão de erros HTTP conhecidos
            # (400, 401, 404, etc.), inclusive os já tratados acima.
            return error

        logger.error("Erro não tratado", exc_info=error)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
