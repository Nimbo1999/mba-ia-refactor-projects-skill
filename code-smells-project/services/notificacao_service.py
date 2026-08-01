"""Envio de notificações relacionadas a pedidos.

Substitui os antigos `print("ENVIANDO EMAIL: ...")` por logging estruturado
e centraliza a orquestração de notificação, que antes vivia misturada no
controller de pedidos.
"""
import logging

logger = logging.getLogger(__name__)


def notificar_novo_pedido(pedido_id, usuario_id):
    logger.info("Notificando novo pedido %s para usuário %s (email/sms/push)", pedido_id, usuario_id)


def notificar_mudanca_status(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado. Preparar envio.", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado. Devolver estoque.", pedido_id)
