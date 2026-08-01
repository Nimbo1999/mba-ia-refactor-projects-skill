"""Entry point / composition root da API da Loja.

Instancia a aplicação, carrega configuração, registra blueprints (rotas) e
middlewares, inicializa o banco e inicia o servidor. Não contém rota nem
lógica de negócio "solta".
"""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import settings
from middlewares.error_handler import registrar as registrar_error_handlers
from models.connection import init_db
from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.sistema_routes import sistema_bp
from routes.usuario_routes import usuario_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["DB_PATH"] = settings.DB_PATH
    app.config["ADMIN_TOKEN"] = settings.ADMIN_TOKEN

    CORS(app, origins=settings.ALLOWED_ORIGINS)

    app.register_blueprint(sistema_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)

    registrar_error_handlers(app)
    init_db(app)

    return app


app = create_app()

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info("Rodando em http://%s:%s", settings.HOST, settings.PORT)
    logger.info("=" * 50)

    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
