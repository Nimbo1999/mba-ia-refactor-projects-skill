from flask import Blueprint

from controllers import sistema_controller as c
from middlewares.auth import requer_autenticacao

sistema_bp = Blueprint("sistema", __name__)

sistema_bp.add_url_rule("/", "index", c.index, methods=["GET"])
sistema_bp.add_url_rule("/health", "health_check", c.health_check, methods=["GET"])
sistema_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", c.relatorio_vendas, methods=["GET"])
sistema_bp.add_url_rule(
    "/admin/reset-db",
    "reset_database",
    requer_autenticacao(papel="admin")(c.reset_database),
    methods=["POST"],
)
