# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

Após o refactor para MVC, a aplicação carrega configuração (secrets, banco, CORS, SMTP) a partir de variáveis de ambiente. Copie o template antes do primeiro boot:

```bash
cp .env.example .env
```

Ajuste os valores em `.env` conforme necessário (em especial `SECRET_KEY`, obrigatório fora de `FLASK_ENV=development`).

### Opção 1: pip + venv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

### Opção 2: uv

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
python seed.py
python app.py
```

Ou, sem ativar o venv manualmente, usando `uv run` diretamente:

```bash
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
uv run python seed.py
uv run python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

> **Nota:** endpoints destrutivos (`DELETE /tasks/<id>`, `DELETE /users/<id>`, `DELETE /categories/<id>`) agora exigem um JWT válido. Faça login em `POST /login` para obter o token e envie-o via header `Authorization: Bearer <token>`.
