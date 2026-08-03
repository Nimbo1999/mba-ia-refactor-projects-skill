from flask import Blueprint

from controllers import user_controller
from middlewares.auth import requer_autenticacao

user_bp = Blueprint('users', __name__)

user_bp.route('/users', methods=['GET'])(user_controller.list_users)
user_bp.route('/users/<int:user_id>', methods=['GET'])(user_controller.get_user)
user_bp.route('/users', methods=['POST'])(user_controller.create_user)
user_bp.route('/users/<int:user_id>', methods=['PUT'])(user_controller.update_user)
user_bp.route('/users/<int:user_id>', methods=['DELETE'])(
    requer_autenticacao()(user_controller.delete_user)
)
user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])(user_controller.get_user_tasks)
user_bp.route('/login', methods=['POST'])(user_controller.login)
