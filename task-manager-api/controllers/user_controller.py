"""Controller da entidade User: orquestra request/response chamando o serviço."""
import logging

from flask import jsonify, request

from database import db
from middlewares.auth import generate_token
from models.task import Task
from models.user import User
from services import user_service

logger = logging.getLogger(__name__)


def list_users():
    users = User.query.all()
    result = []
    for user in users:
        data = user.to_dict()
        data['task_count'] = len(user.tasks)
        result.append(data)
    return jsonify(result), 200


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return jsonify(data), 200


def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    user, error = user_service.create_user(data)
    if error:
        status_code = 409 if 'cadastrado' in error else 400
        return jsonify({'error': error}), status_code

    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return jsonify(user.to_dict()), 201


def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    updated_user, error = user_service.update_user(user, data)
    if error:
        status_code = 409 if 'cadastrado' in error else 400
        return jsonify({'error': error}), status_code

    return jsonify(updated_user.to_dict()), 200


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    for task in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(task)

    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: %s", user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([t.to_dict() for t in tasks]), 200


def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    user, error = user_service.authenticate(email, password)
    if error:
        status_code = 403 if error == 'Usuário inativo' else 401
        return jsonify({'error': error}), status_code

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': generate_token(user),
    }), 200
