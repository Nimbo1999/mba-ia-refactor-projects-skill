"""Utilitários genéricos e reutilizáveis pela aplicação.

Este módulo mantém apenas helpers verdadeiramente transversais (formatação,
parsing de data, geração de id). Regras de validação de negócio (status,
prioridade, papéis, e-mail) vivem em `services/`, próximas da entidade que
governam, para evitar a duplicação que existia aqui antes (ex.: `VALID_STATUSES`
nunca era importado por nenhuma rota).
"""
import uuid
from datetime import datetime


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def sanitize_string(s):
    if s:
        return s.strip()
    return s


def generate_id():
    return str(uuid.uuid4())


def parse_date(date_string):
    for date_format in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_string, date_format)
        except ValueError:
            continue
    return None


def is_valid_color(color):
    return bool(color) and len(color) == 7 and color[0] == '#'

