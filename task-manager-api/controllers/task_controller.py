"""Controller da entidade Task: orquestra request/response chamando o serviço."""
import logging

from flask import jsonify, request

from models.task import Task
from services import task_service

logger = logging.getLogger(__name__)


def list_tasks():
    try:
        return jsonify(task_service.list_tasks_with_relations()), 200
    except Exception:
        logger.exception("Erro ao listar tasks")
        return jsonify({'error': 'Erro interno'}), 500


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task.to_dict()), 200


def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    task, error = task_service.create_task(data)
    if error:
        status_code = 404 if 'não encontrad' in error else 400
        return jsonify({'error': error}), status_code

    logger.info("Task criada: %s - %s", task.id, task.title)
    return jsonify(task.to_dict()), 201


def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    updated_task, error = task_service.update_task(task, data)
    if error:
        status_code = 404 if 'não encontrad' in error else 400
        return jsonify({'error': error}), status_code

    logger.info("Task atualizada: %s", updated_task.id)
    return jsonify(updated_task.to_dict()), 200


def delete_task(task_id):
    from database import db

    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: %s", task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    result = task_service.search_tasks(query, status, priority, user_id)
    return jsonify(result), 200


def task_stats():
    return jsonify(task_service.get_task_stats()), 200
