from flask import Blueprint

from controllers import produto_controller as c

produto_bp = Blueprint("produtos", __name__)

produto_bp.add_url_rule("/produtos", "listar_produtos", c.listar_produtos, methods=["GET"])
produto_bp.add_url_rule("/produtos/busca", "buscar_produtos", c.buscar_produtos, methods=["GET"])
produto_bp.add_url_rule("/produtos/<int:id>", "buscar_produto", c.buscar_produto, methods=["GET"])
produto_bp.add_url_rule("/produtos", "criar_produto", c.criar_produto, methods=["POST"])
produto_bp.add_url_rule("/produtos/<int:id>", "atualizar_produto", c.atualizar_produto, methods=["PUT"])
produto_bp.add_url_rule("/produtos/<int:id>", "deletar_produto", c.deletar_produto, methods=["DELETE"])
