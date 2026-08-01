# Playbook de Refatoração (Fase 3)

> Cada padrão de transformação é mapeado 1:1 (ou N:1) a um item do
> [catálogo de anti-patterns](./02-anti-patterns-catalog.md). Os exemplos de código são apenas
> ilustrativos (Python e/ou JavaScript) — aplique o mesmo conceito na linguagem real do projeto.

## P1 — SQL concatenado → query parametrizada
**Elimina:** C1 (SQL Injection)

```python
# Antes
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

# Depois
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

```javascript
// Antes
db.query(`SELECT * FROM users WHERE id = ${id}`);

// Depois
db.query("SELECT * FROM users WHERE id = ?", [id]);
```

## P2 — Credencial hardcoded → variável de ambiente
**Elimina:** C2 (Credenciais hardcoded)

```python
# Antes
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"

# Depois
import os
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]  # definido em .env, nunca versionado
```

```javascript
// Antes
const JWT_SECRET = "abc123";

// Depois
const JWT_SECRET = process.env.JWT_SECRET;
```

Use `python-dotenv`/`dotenv` (Node) para carregar `.env` em desenvolvimento, e garanta que `.env`
esteja no `.gitignore`. Nunca reexponha o segredo em nenhuma resposta HTTP (ex.: endpoint de
health-check).

## P3 — Endpoint que executa código/SQL arbitrário → remover ou proteger com autenticação forte
**Elimina:** C3 (Endpoint administrativo perigoso)

```python
# Antes
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)  # SQL arbitrário do usuário

# Depois: remover o endpoint. Se uma ferramenta administrativa é realmente necessária,
# exponha apenas operações específicas e parametrizadas, atrás de autenticação + autorização
# de administrador, nunca execução livre de SQL/código vindo do request.
```

Se o endpoint não tiver um propósito de negócio legítimo, a recomendação padrão é **removê-lo**.

## P4 — Senha em texto puro → hash unidirecional
**Elimina:** C4 (Senhas em texto puro)

```python
# Antes
cursor.execute("INSERT INTO usuarios (email, senha) VALUES (?, ?)", (email, senha))
...
"SELECT * FROM usuarios WHERE email = ? AND senha = ?"

# Depois
from werkzeug.security import generate_password_hash, check_password_hash

senha_hash = generate_password_hash(senha)
cursor.execute("INSERT INTO usuarios (email, senha_hash) VALUES (?, ?)", (email, senha_hash))
# no login:
usuario = buscar_por_email(email)
if usuario and check_password_hash(usuario["senha_hash"], senha_informada):
    ...
```

```javascript
// Antes
if (user.password === senhaInformada) { ... }

// Depois
const bcrypt = require("bcrypt");
const senhaHash = await bcrypt.hash(senha, 10);
// no login:
const ok = await bcrypt.compare(senhaInformada, user.passwordHash);
```

## P5 — God Class/Module → split por domínio
**Elimina:** H1 (God Class / God Module)

```python
# Antes: um único models.py com produtos, usuários e pedidos misturados

# Depois:
# models/produto_model.py   -> get_todos_produtos, get_produto_por_id, criar_produto, ...
# models/usuario_model.py   -> get_usuario_por_id, criar_usuario, ...
# models/pedido_model.py    -> criar_pedido, get_pedidos_usuario, ...
```

Cada arquivo resultante deve conter apenas funções/queries relativas a uma única entidade de
negócio, seguindo as [guidelines de arquitetura](./04-architecture-guidelines.md).

## P6 — Endpoint destrutivo sem autenticação → exigir autenticação/autorização
**Elimina:** H2 (Endpoint destrutivo sem auth)

```python
# Antes
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    cursor.execute("DELETE FROM produtos")
    ...

# Depois
@app.route("/admin/reset-db", methods=["POST"])
@requer_autenticacao(papel="admin")
def reset_database():
    ...
```

Implemente `requer_autenticacao` (decorator/middleware) como parte da camada de middlewares,
verificando token/sessão e papel do usuário antes de despachar para o handler.

## P7 — Configuração insegura → configuração por ambiente
**Elimina:** H3 (Configuração insegura de produção)

```python
# Antes
app.config["DEBUG"] = True
CORS(app)  # aberto para qualquer origem

# Depois — config/settings.py
import os
DEBUG = os.environ.get("FLASK_ENV") == "development"
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")
# app.py
app.config["DEBUG"] = settings.DEBUG
CORS(app, origins=settings.ALLOWED_ORIGINS)
```

## P8 — Lógica de negócio no Controller → camada de serviço
**Elimina:** H4 (Lógica de negócio em Controllers/Routes)

```python
# Antes (dentro do controller)
def criar_produto():
    dados = request.get_json()
    categorias_validas = ["informatica", "moveis", "vestuario"]
    if dados["categoria"] not in categorias_validas:
        return jsonify({"erro": "Categoria inválida"}), 400
    ...

# Depois
# services/produto_service.py
CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario"]

def validar_categoria(categoria):
    return categoria in CATEGORIAS_VALIDAS

# controllers/produto_controller.py
def criar_produto():
    dados = request.get_json()
    if not produto_service.validar_categoria(dados["categoria"]):
        return jsonify({"erro": "Categoria inválida"}), 400
    ...
```

## P9 — Estado global mutável → factory/injeção de dependência
**Elimina:** H5 (Estado global mutável)

```python
# Antes
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(...)
    return db_connection

# Depois
def create_connection(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# app.py (composition root)
app.config["DB"] = create_connection(settings.DB_PATH)
# models recebem a conexão via parâmetro/contexto da aplicação, não via variável global importada
```

## P10 — Query N+1 → query única com JOIN/IN
**Elimina:** M1 (Query N+1)

```python
# Antes
for row in pedidos:
    cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (row["id"],))
    ...

# Depois
cursor.execute("""
    SELECT p.*, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    JOIN itens_pedido i ON i.pedido_id = p.id
    JOIN produtos pr ON pr.id = i.produto_id
    WHERE p.usuario_id = ?
""", (usuario_id,))
# agrupar os resultados em memória por pedido_id
```

## P11 — Serialização duplicada → serializer/mapper compartilhado
**Elimina:** M2 (Duplicação de lógica)

```python
# Antes: o mesmo dicionário de campos montado em 3 funções diferentes

# Depois
def serializar_produto(row):
    return {
        "id": row["id"], "nome": row["nome"], "preco": row["preco"],
        "estoque": row["estoque"], "categoria": row["categoria"],
    }
# reutilizado em get_todos_produtos, get_produto_por_id, buscar_produtos
```

## P12 — `print`/`console.log` → logging estruturado
**Elimina:** L1 (Uso de print/console.log)

```python
# Antes
print("ERRO: " + str(e))

# Depois
import logging
logger = logging.getLogger(__name__)
logger.error("Falha ao processar requisição", exc_info=e)
```

```javascript
// Antes
console.log("ERRO: " + e);

// Depois
const logger = require("./config/logger"); // winston/pino configurado
logger.error("Falha ao processar requisição", { error: e });
```

## P13 — Magic numbers → constantes nomeadas
**Elimina:** L2 (Magic numbers)

```python
# Antes
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05

# Depois
FAIXA_DESCONTO_ALTO = 10000
FAIXA_DESCONTO_MEDIO = 5000
PERCENTUAL_DESCONTO_ALTO = 0.10
PERCENTUAL_DESCONTO_MEDIO = 0.05

if faturamento > FAIXA_DESCONTO_ALTO:
    desconto = faturamento * PERCENTUAL_DESCONTO_ALTO
elif faturamento > FAIXA_DESCONTO_MEDIO:
    desconto = faturamento * PERCENTUAL_DESCONTO_MEDIO
```

## P14 — API deprecated → equivalente moderno
**Elimina:** item "Detecção de APIs/padrões deprecated" do catálogo

```python
# Antes (Flask < 2.3)
@app.before_first_request
def setup():
    init_db()

# Depois
with app.app_context():
    init_db()
```

```javascript
// Antes
app.use(express.bodyParser());

// Depois
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
```
