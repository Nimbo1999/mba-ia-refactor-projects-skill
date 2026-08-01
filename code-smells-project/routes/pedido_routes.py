from flask import Blueprint

from controllers import pedido_controller as c

pedido_bp = Blueprint("pedidos", __name__)

pedido_bp.add_url_rule("/pedidos", "criar_pedido", c.criar_pedido, methods=["POST"])
pedido_bp.add_url_rule("/pedidos", "listar_todos_pedidos", c.listar_todos_pedidos, methods=["GET"])
pedido_bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_pedidos_usuario",
    c.listar_pedidos_usuario,
    methods=["GET"],
)
pedido_bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status_pedido",
    c.atualizar_status_pedido,
    methods=["PUT"],
)
