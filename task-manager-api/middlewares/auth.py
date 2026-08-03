"""Middleware de autenticação/autorização baseado em JWT.

Substitui o token fake anterior (`'fake-jwt-token-' + str(user.id)`) por um JWT
assinado com `SECRET_KEY`, validado em todas as rotas destrutivas/sensíveis.
"""
import functools
from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app, jsonify, request


def generate_token(user):
    now = datetime.now(timezone.utc)
    expires_in = current_app.config.get("JWT_EXPIRATION_SECONDS", 28800)
    payload = {
        "sub": user.id,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def _extract_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):].strip()
    return None


def requer_autenticacao(papel=None):
    """Decorator de rota que exige um JWT válido e, opcionalmente, um papel específico."""

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            token = _extract_token()
            if not token:
                return jsonify({"error": "Token de autenticação ausente"}), 401

            try:
                payload = decode_token(token)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expirado"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Token inválido"}), 401

            if papel and payload.get("role") != papel:
                return jsonify({"error": "Permissão insuficiente"}), 403

            request.current_user_id = payload.get("sub")
            request.current_user_role = payload.get("role")
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
