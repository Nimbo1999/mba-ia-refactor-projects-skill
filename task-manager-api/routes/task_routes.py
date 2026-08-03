from flask import Blueprint

from controllers import task_controller
from middlewares.auth import requer_autenticacao

task_bp = Blueprint('tasks', __name__)

task_bp.route('/tasks', methods=['GET'])(task_controller.list_tasks)
task_bp.route('/tasks/search', methods=['GET'])(task_controller.search_tasks)
task_bp.route('/tasks/stats', methods=['GET'])(task_controller.task_stats)
task_bp.route('/tasks/<int:task_id>', methods=['GET'])(task_controller.get_task)
task_bp.route('/tasks', methods=['POST'])(task_controller.create_task)
task_bp.route('/tasks/<int:task_id>', methods=['PUT'])(task_controller.update_task)
task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])(
    requer_autenticacao()(task_controller.delete_task)
)
