"""Regras de negócio para criação e atualização de pedidos.

Orquestra a leitura de produtos (evitando N+1 com `get_por_ids`), validação
de estoque, cálculo do total e disparo de notificações — lógica que antes
estava espalhada entre `controllers.py` e `models.py`.
"""
from models import pedido_model, produto_model
from services import notificacao_service

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar_pedido(usuario_id, itens):
    produtos_ids = [item["produto_id"] for item in itens]
    produtos_por_id = produto_model.get_por_ids(produtos_ids)

    total = 0
    itens_processados = []

    for item in itens:
        produto = produtos_por_id.get(item["produto_id"])
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}

        total += produto["preco"] * item["quantidade"]
        itens_processados.append(
            {
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
            }
        )

    pedido_id = pedido_model.criar(usuario_id, total, itens_processados)
    notificacao_service.notificar_novo_pedido(pedido_id, usuario_id)

    return {"pedido_id": pedido_id, "total": total}


def atualizar_status_pedido(pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        return {"erro": "Status inválido"}

    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.notificar_mudanca_status(pedido_id, novo_status)
    return {"sucesso": True}
