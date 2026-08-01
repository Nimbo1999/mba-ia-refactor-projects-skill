"""Acesso a dados da entidade Pedido.

`get_por_usuario`/`get_todos` usam uma única query com JOIN para montar
pedidos + itens + nome do produto, eliminando o N+1 do código original
(um SELECT por item dentro de um laço por pedido).
"""
from models.connection import get_db

_QUERY_BASE = """
    SELECT
        p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
        i.produto_id, i.quantidade, i.preco_unitario,
        pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar_por_pedido(rows):
    pedidos = {}
    ordem = []
    for row in rows:
        pedido_id = row["pedido_id"]
        if pedido_id not in pedidos:
            pedidos[pedido_id] = {
                "id": pedido_id,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            ordem.append(pedido_id)
        if row["produto_id"] is not None:
            pedidos[pedido_id]["itens"].append(
                {
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                }
            )
    return [pedidos[pedido_id] for pedido_id in ordem]


def criar(usuario_id, total, itens_processados):
    """Persiste o pedido e seus itens, e dá baixa no estoque.

    Recebe os itens já validados/processados (com preço unitário resolvido)
    pela camada de serviço — este model não decide regras de negócio, apenas
    grava o resultado de forma atômica.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens_processados:
        cursor.execute(
            """
            INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
            """,
            (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return pedido_id


def get_por_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(_QUERY_BASE + " WHERE p.usuario_id = ? ORDER BY p.id", (usuario_id,))
    return _agrupar_por_pedido(cursor.fetchall())


def get_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(_QUERY_BASE + " ORDER BY p.id")
    return _agrupar_por_pedido(cursor.fetchall())


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
    )
    db.commit()
    return True


def obter_estatisticas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM pedidos")
    total_pedidos, faturamento = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("pendente",))
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("aprovado",))
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("cancelado",))
    cancelados = cursor.fetchone()[0]

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": faturamento,
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
    }
