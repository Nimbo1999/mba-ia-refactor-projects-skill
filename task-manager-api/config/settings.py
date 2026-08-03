"""Configuração centralizada por ambiente.

Nenhum segredo deve ficar hardcoded no código-fonte: todos os valores sensíveis
vêm de variáveis de ambiente (carregadas de um `.env` local em desenvolvimento
via python-dotenv, ou do ambiente real em produção).
"""
import os

from dotenv import load_dotenv

load_dotenv()

FLASK_ENV = os.environ.get("FLASK_ENV", "production")
DEBUG = FLASK_ENV == "development"

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        # Apenas para conveniência local; nunca usado fora de FLASK_ENV=development.
        SECRET_KEY = "dev-only-insecure-secret-key"
    else:
        raise RuntimeError(
            "SECRET_KEY não definido. Configure a variável de ambiente SECRET_KEY "
            "antes de subir a aplicação em produção."
        )

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

_default_origins = "http://localhost:3000" if DEBUG else ""
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

JWT_EXPIRATION_SECONDS = int(os.environ.get("JWT_EXPIRATION_SECONDS", str(60 * 60 * 8)))

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
