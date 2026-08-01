"""Controller de Usuários: orquestra request -> service/model -> resposta."""
import logging

from flask import jsonify, request

from models import usuario_model
from services import usuario_service

logger = logging.getLogger(__name__)


def listar_usuarios():
    try:
        usuarios = usuario_model.get_todos()
        return jsonify({"dados": usuarios, "sucesso": True}), 200
    except Exception as e:
        logger.error("Erro ao listar usuários", exc_info=e)
        return jsonify({"erro": str(e)}), 500


def buscar_usuario(id):
    try:
        usuario = usuario_model.get_por_id(id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        logger.error("Erro ao buscar usuário %s", id, exc_info=e)
        return jsonify({"erro": str(e)}), 500


def criar_usuario():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        erros = usuario_service.validar_dados_usuario(nome, email, senha)
        if erros:
            return jsonify({"erro": erros[0]}), 400

        id = usuario_service.criar_usuario(nome, email, senha)
        logger.info("Usuário criado: %s", email)
        return jsonify({"dados": {"id": id}, "sucesso": True}), 201
    except Exception as e:
        logger.error("Erro ao criar usuário", exc_info=e)
        return jsonify({"erro": str(e)}), 500


def login():
    try:
        dados = request.get_json()
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = usuario_service.autenticar(email, senha)
        if usuario:
            logger.info("Login bem-sucedido: %s", email)
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

        logger.info("Login falhou: %s", email)
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    except Exception as e:
        logger.error("Erro no login", exc_info=e)
        return jsonify({"erro": str(e)}), 500
