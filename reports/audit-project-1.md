================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib, driver de persistência)
Domain:        API de E-commerce — produtos, usuários, pedidos/itens de pedido, login e relatório de vendas
Architecture:  Monolítica com pseudo-separação em 3 arquivos (app.py = rotas + 2 endpoints admin com lógica embutida, controllers.py = camada de apresentação/validação, models.py = acesso a dados via SQL cru concatenado); sem camada de configuração/serviço separada, sem tratamento de erro centralizado, entry point único em app.py
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

<br/>
<br/>
<br/>

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] SQL Injection
File: models.py:28, 47-50, 68, 92, 109-111, 126-129, 140-166, 174-224, 279-297
Description: Praticamente todas as funções de acesso a dados montam queries SQL concatenando strings com valores vindos diretamente de parâmetros de função (id, nome, email, senha, categoria, termo de busca), sem usar placeholders (`?`).
Impact: Qualquer input de usuário (ex.: `id`, `termo`, `email`, `senha`) pode injetar SQL arbitrário, permitindo leitura/alteração/exclusão não autorizada de dados de todo o banco.
Recommendation: Substituir toda concatenação por queries parametrizadas (`cursor.execute("... WHERE id = ?", (id,))`), seguindo o playbook de eliminação de SQL Injection.

### [CRITICAL] Hardcoded Credentials
File: app.py:7; controllers.py:289
Description: A `SECRET_KEY` do Flask é um literal fixo no código-fonte versionado e, além disso, é reexposta em texto puro na resposta JSON do endpoint `/health`.
Impact: Qualquer pessoa com acesso ao repositório ou ao endpoint de health-check obtém a chave secreta, permitindo forjar sessões/tokens assinados pela aplicação.
Recommendation: Mover a secret key para variável de ambiente (`os.environ["SECRET_KEY"]`) e remover completamente seu valor da resposta do health-check.

### [CRITICAL] Endpoint administrativo executa SQL arbitrário sem autenticação
File: app.py:59-78
Description: A rota `POST /admin/query` recebe uma string SQL livre do corpo da requisição e a executa diretamente contra o banco, sem nenhuma verificação de identidade ou papel.
Impact: Qualquer cliente não autenticado pode ler, alterar ou apagar qualquer dado do banco, incluindo tabelas de usuários e senhas — comprometimento total do sistema.
Recommendation: Remover o endpoint ou, se estritamente necessário para operação interna, protegê-lo com autenticação forte + autorização de administrador e eliminar a execução de SQL livre.

### [CRITICAL] Senhas armazenadas e comparadas em texto puro
File: models.py:105-120, 122-131; database.py:75-79
Description: Senhas de usuário são gravadas (`criar_usuario`) e comparadas no login (`login_usuario`) como texto puro, incluindo os dados de seed (`admin123`, `123456`, `senha123`).
Impact: Um vazamento de banco (facilitado pelo C1/C3 acima) expõe as senhas de todos os usuários em claro, permitindo reuso em outros sistemas.
Recommendation: Aplicar hash com `werkzeug.security.generate_password_hash`/`check_password_hash` (ou bcrypt) antes de persistir e ao validar login.

### [HIGH] God Module
File: controllers.py:1-292; models.py:1-314
Description: Dois arquivos monolíticos concentram, cada um, lógica de produtos, usuários, pedidos e relatórios — 4+ domínios de negócio distintos sem qualquer separação em módulos/pastas.
Impact: Alterações em uma entidade arriscam efeitos colaterais nas demais; dificulta testes isolados e a localização de responsabilidades.
Recommendation: Dividir em módulos por domínio (`models/produto.py`, `models/usuario.py`, `models/pedido.py`, controllers equivalentes), conforme `04-architecture-guidelines.md`.

### [HIGH] Endpoint destrutivo sem autenticação/autorização
File: app.py:47-57
Description: A rota `POST /admin/reset-db` apaga todos os registros de `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem exigir nenhuma credencial.
Impact: Qualquer requisição não autenticada pode destruir a base de dados de produção completamente.
Recommendation: Remover o endpoint de produção ou protegê-lo com autenticação de administrador e restrição de ambiente (ex.: apenas em `ENV=development`).

### [HIGH] Configuração insegura de produção
File: app.py:8-9, 88
Description: `DEBUG = True` está fixo no config, `CORS(app)` é habilitado sem restrição de origem, e `app.run(..., debug=True)` é usado no entry point, mesmo o health-check declarando `"ambiente": "producao"`.
Impact: Modo debug expõe stack traces e permite execução de código via debugger do Werkzeug; CORS aberto permite qualquer origem chamar a API.
Recommendation: Controlar `debug`/CORS por variável de ambiente, desabilitando-os por padrão e restringindo `origins` explicitamente em produção.

### [HIGH] Lógica de negócio dentro de Controllers
File: controllers.py:24-96, 203-220
Description: Validações de negócio extensas (regras de preço/estoque/categoria) e orquestração de efeitos colaterais (disparo de "email"/"SMS"/"push" via `print`) ficam diretamente nos handlers de rota, em vez de uma camada de serviço.
Impact: Regras de negócio ficam duplicadas entre `criar_produto`/`atualizar_produto` e não são testáveis isoladamente da camada HTTP.
Recommendation: Extrair validação e orquestração para uma camada de serviço (`services/produto_service.py`, `services/pedido_service.py`, `services/notificacao_service.py`).

### [HIGH] Estado global mutável / forte acoplamento sem injeção de dependência
File: database.py:4, 7-10; models.py:1; app.py:4
Description: `db_connection` é uma variável global de módulo, reatribuída dentro do "getter" `get_db()` e importada diretamente por `models.py` e `app.py`, sem nenhuma abstração de injeção de dependência.
Impact: Impossibilita testes com banco isolado/mockado e cria acoplamento rígido entre todas as camadas e uma única conexão global.
Recommendation: Encapsular a conexão em uma factory/config de aplicação (`app.config`, `Flask-SQLAlchemy` engine, ou context manager por request).

### [MEDIUM] Query N+1
File: models.py:171-201, 203-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` abrem um novo cursor dentro de laços aninhados (um `SELECT` por item de pedido e outro por produto) em vez de usar `JOIN`.
Impact: Degradação de performance proporcional ao número de pedidos/itens, especialmente em `listar_todos_pedidos`.
Recommendation: Substituir por uma única query com `JOIN` entre `pedidos`, `itens_pedido` e `produtos`, agrupando os resultados em memória.

### [MEDIUM] Duplicação de lógica de serialização
File: models.py:10-21, 30-40, 302-313, 177-199, 209-231
Description: O mapeamento de linha de banco para dicionário de resposta (produto e pedido) é reescrito de forma idêntica em múltiplas funções.
Impact: Qualquer mudança de schema/campo exige atualizar várias funções manualmente, com risco de inconsistência.
Recommendation: Centralizar em funções `serializar_produto(row)`/`serializar_pedido(row, itens)` reutilizadas por todas as funções de leitura.

### [MEDIUM] Ausência de validação de entrada em rotas
File: controllers.py:146-165
Description: `criar_usuario` valida apenas presença de `nome`/`email`/`senha`, sem checar formato de email nem requisitos mínimos de senha.
Impact: Permite cadastro de emails inválidos e senhas triviais, comprometendo qualidade dos dados e segurança da conta.
Recommendation: Adicionar validação de formato (regex de email) e política mínima de senha antes de delegar ao model.

### [LOW] Uso de print para logging
File: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210
Description: Diagnósticos e eventos de aplicação (erros, criação de recursos, login, notificações) são emitidos via `print(...)` em vez de um logger configurável.
Impact: Sem níveis de log, formatação ou destino configurável, dificultando observabilidade em produção.
Recommendation: Substituir por `logging` configurado (`logging.getLogger(__name__)`), com níveis apropriados (`info`, `error`).

### [LOW] Magic numbers
File: models.py:257-262; controllers.py:49-50
Description: Limiares de desconto (`10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02`) e limite de tamanho de nome (`200`) aparecem soltos no meio da lógica, sem constantes nomeadas.
Impact: Reduz legibilidade e dificulta ajuste consistente das regras de negócio.
Recommendation: Extrair para constantes nomeadas (ex.: `DESCONTO_FATURAMENTO_ALTO = 0.1`, `NOME_MAX_LENGTH = 200`).

### [LOW] Nomenclatura pouco descritiva
File: models.py:187, 191, 219, 223
Description: Cursores adicionais dentro dos laços de `get_pedidos_usuario`/`get_todos_pedidos` são nomeados `cursor2`/`cursor3`, sem comunicar seu propósito.
Impact: Reduz legibilidade e dificulta o entendimento do fluxo de dados aninhado.
Recommendation: Renomear para nomes descritivos (ex.: `cursor_itens`, `cursor_produto`) ou eliminar via refatoração do N+1 acima.

================================
Total: 15 findings
================================

<br/>
<br/>
<br/>

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── .env                       # secrets locais (SECRET_KEY, ADMIN_TOKEN) — não versionado
├── .env.example               # template de variáveis de ambiente
├── app.py                     # entry point / composition root (create_app, CORS, blueprints)
├── config/
│   └── settings.py            # leitura de env vars (SECRET_KEY, DEBUG, CORS, DB_PATH, ADMIN_TOKEN)
├── models/
│   ├── connection.py           # conexão por-request via flask.g (substitui global mutável)
│   ├── produto_model.py        # queries parametrizadas + serializer de Produto
│   ├── usuario_model.py        # queries parametrizadas de Usuário (senha_hash nunca serializada)
│   └── pedido_model.py         # queries parametrizadas + JOIN (elimina N+1) de Pedido
├── services/
│   ├── produto_service.py      # validação de categoria/preço/estoque/nome
│   ├── usuario_service.py      # validação de email/senha + hashing (werkzeug)
│   ├── pedido_service.py       # cálculo de total, checagem de estoque, orquestração
│   ├── relatorio_service.py    # regras de desconto com constantes nomeadas
│   └── notificacao_service.py  # logging estruturado de notificações (email/sms/push)
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   └── sistema_controller.py   # index, health, relatório, admin/reset-db (protegido)
├── routes/
│   ├── produto_routes.py / usuario_routes.py / pedido_routes.py / sistema_routes.py
├── middlewares/
│   ├── auth.py                 # requer_autenticacao (protege /admin/reset-db)
│   └── error_handler.py        # tratamento de erro centralizado, sem vazamento de stack trace
└── requirements.txt            # + python-dotenv

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly (index, health, produtos CRUD, busca, login, usuarios,
    pedidos com JOIN, relatório de vendas, admin/reset-db com/sem token)
  ✓ Zero anti-patterns remaining
================================
