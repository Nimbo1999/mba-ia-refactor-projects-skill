# code-smells-project

API de E-commerce em Python/Flask, estruturada em MVC (`models/`, `controllers/`, `routes/`,
`services/`, `middlewares/`, `config/`).

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # ou: uv venv && source .venv/bin/activate
pip install -r requirements.txt                      # ou: uv pip install -r requirements.txt
cp .env.example .env                                 # defina SECRET_KEY e ADMIN_TOKEN
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente
no primeiro boot, já com produtos e usuários de exemplo (senhas armazenadas com hash).

## Configuração

Todas as configurações sensíveis vêm de variáveis de ambiente (ver `.env.example`):

- `SECRET_KEY`: chave secreta do Flask.
- `ADMIN_TOKEN`: token exigido no header `X-Admin-Token` para endpoints administrativos
  (ex.: `POST /admin/reset-db`).
- `FLASK_DEBUG`: `true`/`false` (padrão `false`).
- `ALLOWED_ORIGINS`: lista de origens permitidas por CORS, separadas por vírgula.
- `DB_PATH`: caminho do arquivo SQLite.
