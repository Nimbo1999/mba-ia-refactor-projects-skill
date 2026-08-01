"""Cálculo do relatório de vendas: descontos escalonados por faixa de
faturamento, com constantes nomeadas em vez de magic numbers."""
from models import pedido_model

FAIXA_DESCONTO_ALTO = 10000
FAIXA_DESCONTO_MEDIO = 5000
FAIXA_DESCONTO_BAIXO = 1000

PERCENTUAL_DESCONTO_ALTO = 0.10
PERCENTUAL_DESCONTO_MEDIO = 0.05
PERCENTUAL_DESCONTO_BAIXO = 0.02


def _calcular_desconto(faturamento):
    if faturamento > FAIXA_DESCONTO_ALTO:
        return faturamento * PERCENTUAL_DESCONTO_ALTO
    if faturamento > FAIXA_DESCONTO_MEDIO:
        return faturamento * PERCENTUAL_DESCONTO_MEDIO
    if faturamento > FAIXA_DESCONTO_BAIXO:
        return faturamento * PERCENTUAL_DESCONTO_BAIXO
    return 0


def gerar_relatorio_vendas():
    estatisticas = pedido_model.obter_estatisticas()
    faturamento = estatisticas["faturamento_bruto"]
    total_pedidos = estatisticas["total_pedidos"]

    desconto = _calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": estatisticas["pedidos_pendentes"],
        "pedidos_aprovados": estatisticas["pedidos_aprovados"],
        "pedidos_cancelados": estatisticas["pedidos_cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
