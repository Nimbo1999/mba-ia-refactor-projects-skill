"""Acesso a dados da entidade Usuário.

`senha_hash` nunca é exposta em `_serializar` (usado pelas rotas públicas);
`get_por_email` retorna a linha crua, usada apenas internamente pela camada
de serviço para verificar a senha com hash.
"""
from models.connection import get_db


def _serializar(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_serializar(row) for row in cursor.fetchall()]


def get_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _serializar(row) if row else None


def get_por_email(email):
    """Retorna a linha crua (incluindo senha_hash) para uso exclusivo da
    camada de serviço durante autenticação. Nunca repassar diretamente para
    uma resposta HTTP."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    return cursor.fetchone()


def criar(nome, email, senha_hash, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid
