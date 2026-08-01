"""Regras de negócio da entidade Produto (extraídas dos controllers)."""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
NOME_MIN_LENGTH = 2
NOME_MAX_LENGTH = 200


def validar_dados_produto(dados):
    """Retorna uma lista de mensagens de erro (vazia se os dados forem válidos)."""
    erros = []

    nome = dados.get("nome", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")
    categoria = dados.get("categoria", "geral")

    if preco is not None and preco < 0:
        erros.append("Preço não pode ser negativo")
    if estoque is not None and estoque < 0:
        erros.append("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN_LENGTH:
        erros.append("Nome muito curto")
    if len(nome) > NOME_MAX_LENGTH:
        erros.append("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    return erros
