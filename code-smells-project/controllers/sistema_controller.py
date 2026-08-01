"""Controller de endpoints de sistema: boas-vindas, health-check, relatório e
administração (protegida por autenticação)."""
import logging

from flask import current_app, jsonify

from models.connection import get_db
from services import relatorio_service

logger = logging.getLogger(__name__)


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]

        return (
            jsonify(
                {
                    "status": "ok",
                    "database": "connected",
                    "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
                    "versao": "1.0.0",
                    "ambiente": "development" if current_app.config.get("DEBUG") else "production",
                }
            ),
            200,
        )
    except Exception as e:
        logger.error("Erro no health check", exc_info=e)
        return jsonify({"status": "erro", "detalhes": str(e)}), 500


def relatorio_vendas():
    try:
        relatorio = relatorio_service.gerar_relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception as e:
        logger.error("Erro ao gerar relatório de vendas", exc_info=e)
        return jsonify({"erro": str(e)}), 500


def reset_database():
    """Endpoint administrativo protegido (ver middlewares.auth)."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
