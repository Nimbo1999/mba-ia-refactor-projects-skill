"""Controller de Produtos: orquestra request -> service/model -> resposta.

Sem SQL e sem regra de negócio pesada aqui — validações de domínio ficam em
`services.produto_service`.
"""
import logging

from flask import jsonify, request

from models import produto_model
from services import produto_service

logger = logging.getLogger(__name__)


def listar_produtos():
    try:
        produtos = produto_model.get_todos()
        logger.info("Listando %d produtos", len(produtos))
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        logger.error("Erro ao listar produtos", exc_info=e)
        return jsonify({"erro": str(e)}), 500


def buscar_produto(id):
    try:
        produto = produto_model.get_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        logger.error("Erro ao buscar produto %s", id, exc_info=e)
        return jsonify({"erro": str(e)}), 500


def criar_produto():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        campos_obrigatorios = ["nome", "preco", "estoque"]
        faltando = [campo for campo in campos_obrigatorios if campo not in dados]
        if faltando:
            return jsonify({"erro": f"{faltando[0].capitalize()} é obrigatório"}), 400

        erros = produto_service.validar_dados_produto(dados)
        if erros:
            return jsonify({"erro": erros[0]}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        id = produto_model.criar(nome, descricao, preco, estoque, categoria)
        logger.info("Produto criado com ID: %s", id)
        return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201
    except Exception as e:
        logger.error("Erro ao criar produto", exc_info=e)
        return jsonify({"erro": str(e)}), 500


def atualizar_produto(id):
    try:
        dados = request.get_json()

        produto_existente = produto_model.get_por_id(id)
        if not produto_existente:
            return jsonify({"erro": "Produto não encontrado"}), 404

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        campos_obrigatorios = ["nome", "preco", "estoque"]
        faltando = [campo for campo in campos_obrigatorios if campo not in dados]
        if faltando:
            return jsonify({"erro": f"{faltando[0].capitalize()} é obrigatório"}), 400

        erros = produto_service.validar_dados_produto(dados)
        if erros:
            return jsonify({"erro": erros[0]}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        produto_model.atualizar(id, nome, descricao, preco, estoque, categoria)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except Exception as e:
        logger.error("Erro ao atualizar produto %s", id, exc_info=e)
        return jsonify({"erro": str(e)}), 500


def deletar_produto(id):
    try:
        produto = produto_model.get_por_id(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        produto_model.deletar(id)
        logger.info("Produto %s deletado", id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception as e:
        logger.error("Erro ao deletar produto %s", id, exc_info=e)
        return jsonify({"erro": str(e)}), 500


def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception as e:
        logger.error("Erro ao buscar produtos", exc_info=e)
        return jsonify({"erro": str(e)}), 500
