"""Camada de serviço para a entidade User."""
import re

from database import db
from models.user import USER_ROLES, User

MIN_PASSWORD_LENGTH = 4
EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'


def validate_email_format(email):
    return bool(re.match(EMAIL_REGEX, email))


def validate_user_payload(data, partial=False, current_user_id=None):
    """Valida os campos de um usuário. Retorna (cleaned_data, error_message)."""
    cleaned = {}

    if not partial or 'name' in data:
        name = data.get('name')
        if not partial and not name:
            return None, 'Nome é obrigatório'
        if name is not None:
            cleaned['name'] = name

    if not partial or 'email' in data:
        email = data.get('email')
        if not partial and not email:
            return None, 'Email é obrigatório'
        if email is not None:
            if not validate_email_format(email):
                return None, 'Email inválido'
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != current_user_id:
                return None, 'Email já cadastrado'
            cleaned['email'] = email

    if not partial or 'password' in data:
        password = data.get('password')
        if not partial and not password:
            return None, 'Senha é obrigatória'
        if password is not None:
            if len(password) < MIN_PASSWORD_LENGTH:
                return None, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'
            cleaned['password'] = password

    if 'role' in data or not partial:
        role = data.get('role', 'user' if not partial else None)
        if role is not None:
            if role not in USER_ROLES:
                return None, 'Role inválido'
            cleaned['role'] = role

    if 'active' in data:
        cleaned['active'] = data['active']

    return cleaned, None


def create_user(data):
    cleaned, error = validate_user_payload(data, partial=False)
    if error:
        return None, error

    password = cleaned.pop('password')
    user = User(**cleaned)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user, None


def update_user(user, data):
    cleaned, error = validate_user_payload(data, partial=True, current_user_id=user.id)
    if error:
        return None, error

    password = cleaned.pop('password', None)
    for field, value in cleaned.items():
        setattr(user, field, value)
    if password:
        user.set_password(password)

    db.session.commit()
    return user, None


def authenticate(email, password):
    """Retorna (user, error_message)."""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return None, 'Credenciais inválidas'
    if not user.active:
        return None, 'Usuário inativo'
    return user, None
