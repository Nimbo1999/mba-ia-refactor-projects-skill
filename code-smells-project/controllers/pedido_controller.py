"""Controller de Pedidos: orquestra request -> service/model -> resposta.

Cálculo de total, checagem de estoque e notificações foram movidos para
`services.pedido_service` — este controller apenas valida a forma da
requisição e delega o fluxo de negócio.
"""
import logging

from flask import jsonify, request

from models import pedido_model
from services import pedido_service

logger = logging.getLogger(__name__)


def criar_pedido():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = pedido_service.criar_pedido(usuario_id, itens)

        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        return (
            jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}),
            201,
        )
    except Exception as e:
        logger.error("Erro crítico ao criar pedido", exc_info=e)
        return jsonify({"erro": str(e)}), 500


def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = pedido_model.get_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error("Erro ao listar pedidos do usuário %s", usuario_id, exc_info=e)
        return jsonify({"erro": str(e)}), 500


def listar_todos_pedidos():
    try:
        pedidos = pedido_model.get_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error("Erro ao listar pedidos", exc_info=e)
        return jsonify({"erro": str(e)}), 500


def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json()
        novo_status = dados.get("status", "")

        resultado = pedido_service.atualizar_status_pedido(pedido_id, novo_status)
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"]}), 400

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
    except Exception as e:
        logger.error("Erro ao atualizar status do pedido %s", pedido_id, exc_info=e)
        return jsonify({"erro": str(e)}), 500
