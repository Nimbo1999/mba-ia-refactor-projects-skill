"""Configuração central de logging estruturado para a aplicação."""
import logging


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_logger(name):
    return logging.getLogger(name)
