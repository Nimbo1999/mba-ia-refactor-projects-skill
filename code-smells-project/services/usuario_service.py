"""Regras de negócio da entidade Usuário: hashing de senha e autenticação."""
import re

from werkzeug.security import check_password_hash, generate_password_hash

from models import usuario_model

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SENHA_MIN_LENGTH = 6


def validar_dados_usuario(nome, email, senha):
    erros = []
    if not nome or not email or not senha:
        erros.append("Nome, email e senha são obrigatórios")
        return erros

    if not _EMAIL_REGEX.match(email):
        erros.append("Email inválido")
    if len(senha) < SENHA_MIN_LENGTH:
        erros.append(f"Senha deve ter pelo menos {SENHA_MIN_LENGTH} caracteres")

    return erros


def criar_usuario(nome, email, senha, tipo="cliente"):
    senha_hash = generate_password_hash(senha)
    return usuario_model.criar(nome, email, senha_hash, tipo)


def autenticar(email, senha):
    usuario = usuario_model.get_por_email(email)
    if usuario and check_password_hash(usuario["senha_hash"], senha):
        return {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "tipo": usuario["tipo"],
        }
    return None
