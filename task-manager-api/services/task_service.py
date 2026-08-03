"""Camada de serviço para a entidade Task.

Centraliza validação e orquestração de regras de negócio que antes estavam
espalhadas (e duplicadas) diretamente nos handlers de rota.
"""
from datetime import datetime

from database import db
from models.category import Category
from models.task import TASK_STATUSES, MAX_PRIORITY, MIN_PRIORITY, Task
from models.user import User

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200


def _parse_due_date(raw_value):
    return datetime.strptime(raw_value, '%Y-%m-%d')


def _normalize_tags(tags):
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def validate_task_payload(data, partial=False):
    """Valida os campos de uma task. Retorna (cleaned_data, error_message)."""
    cleaned = {}

    if not partial or 'title' in data:
        title = data.get('title')
        if not title:
            return None, 'Título é obrigatório'
        if len(title) < MIN_TITLE_LENGTH:
            return None, 'Título muito curto'
        if len(title) > MAX_TITLE_LENGTH:
            return None, 'Título muito longo'
        cleaned['title'] = title

    if 'description' in data:
        cleaned['description'] = data['description']

    if not partial or 'status' in data:
        status = data.get('status', 'pending' if not partial else None)
        if status is not None:
            if status not in TASK_STATUSES:
                return None, 'Status inválido'
            cleaned['status'] = status

    if not partial or 'priority' in data:
        priority = data.get('priority', 3 if not partial else None)
        if priority is not None:
            if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
                return None, f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}'
            cleaned['priority'] = priority

    if 'user_id' in data:
        user_id = data['user_id']
        if user_id:
            if not User.query.get(user_id):
                return None, 'Usuário não encontrado'
        cleaned['user_id'] = user_id

    if 'category_id' in data:
        category_id = data['category_id']
        if category_id:
            if not Category.query.get(category_id):
                return None, 'Categoria não encontrada'
        cleaned['category_id'] = category_id

    if 'due_date' in data:
        due_date = data['due_date']
        if due_date:
            try:
                cleaned['due_date'] = _parse_due_date(due_date)
            except ValueError:
                return None, 'Formato de data inválido. Use YYYY-MM-DD'
        else:
            cleaned['due_date'] = None

    if 'tags' in data:
        cleaned['tags'] = _normalize_tags(data['tags'])

    return cleaned, None


def create_task(data):
    cleaned, error = validate_task_payload(data, partial=False)
    if error:
        return None, error

    task = Task(**cleaned)
    db.session.add(task)
    db.session.commit()
    return task, None


def update_task(task, data):
    cleaned, error = validate_task_payload(data, partial=True)
    if error:
        return None, error

    for field, value in cleaned.items():
        setattr(task, field, value)

    db.session.commit()
    return task, None


def list_tasks_with_relations():
    """Lista tasks com nome de usuário/categoria em uma única query (evita N+1)."""
    rows = (
        db.session.query(Task, User.name, Category.name)
        .outerjoin(User, Task.user_id == User.id)
        .outerjoin(Category, Task.category_id == Category.id)
        .all()
    )

    result = []
    for task, user_name, category_name in rows:
        data = task.to_dict()
        data['user_name'] = user_name
        data['category_name'] = category_name
        result.append(data)
    return result


def search_tasks(query, status, priority, user_id):
    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return [t.to_dict() for t in tasks.all()]


def get_task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
