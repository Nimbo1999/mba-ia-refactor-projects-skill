from flask import Blueprint

from controllers import usuario_controller as c

usuario_bp = Blueprint("usuarios", __name__)

usuario_bp.add_url_rule("/usuarios", "listar_usuarios", c.listar_usuarios, methods=["GET"])
usuario_bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario", c.buscar_usuario, methods=["GET"])
usuario_bp.add_url_rule("/usuarios", "criar_usuario", c.criar_usuario, methods=["POST"])
usuario_bp.add_url_rule("/login", "login", c.login, methods=["POST"])
