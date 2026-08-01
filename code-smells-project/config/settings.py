"""Configuração da aplicação, carregada a partir de variáveis de ambiente.

Nenhum segredo é hardcoded aqui: valores sensíveis vêm sempre de variáveis de
ambiente (opcionalmente carregadas de um arquivo `.env` em desenvolvimento).
"""
import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _build_secret_key() -> str:
    secret_key = os.environ.get("SECRET_KEY")
    if secret_key:
        return secret_key

    logger.warning(
        "SECRET_KEY não definida em variável de ambiente. Usando valor aleatório "
        "gerado em tempo de execução (sessões serão invalidadas a cada restart). "
        "Defina SECRET_KEY no .env para produção."
    )
    return secrets.token_hex(32)


class Settings:
    SECRET_KEY = _build_secret_key()
    DEBUG = os.environ.get("FLASK_DEBUG", "false").strip().lower() == "true"
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))


settings = Settings()
