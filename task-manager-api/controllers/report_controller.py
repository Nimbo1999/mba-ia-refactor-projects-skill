"""Controller de relatórios e categorias."""
from datetime import datetime, timedelta, timezone

from flask import jsonify, request

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, format_date


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    priority_counts = {
        p: Task.query.filter_by(priority=p).count() for p in range(1, 6)
    }

    overdue_tasks = [t for t in Task.query.all() if t.is_overdue()]
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': format_date(t.due_date),
            'days_overdue': (_utcnow() - t.due_date).days,
        }
        for t in overdue_tasks
    ]

    seven_days_ago = _utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago,
    ).count()

    user_stats = []
    for user in User.query.all():
        user_tasks = Task.query.filter_by(user_id=user.id).all()
        total = len(user_tasks)
        completed = sum(1 for t in user_tasks if t.status == 'done')
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    report = {
        'generated_at': format_date(_utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': priority_counts[1],
            'high': priority_counts[2],
            'medium': priority_counts[3],
            'low': priority_counts[4],
            'minimal': priority_counts[5],
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }

    return jsonify(report), 200


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()

    status_counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    high_priority = 0
    overdue = 0

    for task in tasks:
        if task.status in status_counts:
            status_counts[task.status] += 1
        if task.priority <= 2:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    total = len(tasks)
    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': status_counts['done'],
            'pending': status_counts['pending'],
            'in_progress': status_counts['in_progress'],
            'cancelled': status_counts['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(status_counts['done'], total),
        },
    }

    return jsonify(report), 200


def list_categories():
    categories = Category.query.all()
    result = []
    for category in categories:
        data = category.to_dict()
        data['task_count'] = Task.query.filter_by(category_id=category.id).count()
        result.append(data)
    return jsonify(result), 200


def create_category():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name')
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    color = data.get('color', '#000000')
    category = Category(name=name, description=data.get('description', ''), color=color)
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


def update_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    db.session.commit()
    return jsonify(category.to_dict()), 200


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Categoria deletada'}), 200
