"""Autenticação simples para endpoints administrativos.

O código original não tinha nenhum mecanismo de autenticação. Para eliminar
o anti-pattern "endpoint destrutivo sem autenticação" sem inventar um
sistema de sessão/JWT completo fora do escopo deste refactor, adota-se um
token de administrador fixo por variável de ambiente (`ADMIN_TOKEN`),
enviado no header `X-Admin-Token`.
"""
from functools import wraps

from flask import current_app, jsonify, request


def requer_autenticacao(papel="admin"):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token_esperado = current_app.config.get("ADMIN_TOKEN")
            token_recebido = request.headers.get("X-Admin-Token")

            if not token_esperado or token_recebido != token_esperado:
                return jsonify({"erro": "Não autorizado", "sucesso": False}), 401

            return f(*args, **kwargs)

        return wrapper

    return decorator
