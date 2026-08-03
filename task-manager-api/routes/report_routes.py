from flask import Blueprint

from controllers import report_controller
from middlewares.auth import requer_autenticacao

report_bp = Blueprint('reports', __name__)

report_bp.route('/reports/summary', methods=['GET'])(report_controller.summary_report)
report_bp.route('/reports/user/<int:user_id>', methods=['GET'])(report_controller.user_report)
report_bp.route('/categories', methods=['GET'])(report_controller.list_categories)
report_bp.route('/categories', methods=['POST'])(report_controller.create_category)
report_bp.route('/categories/<int:cat_id>', methods=['PUT'])(report_controller.update_category)
report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])(
    requer_autenticacao()(report_controller.delete_category)
)
