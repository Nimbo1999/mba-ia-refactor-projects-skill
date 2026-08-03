================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.0.0 (+ Flask-SQLAlchemy 3.1.1)
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0 (marshmallow==3.20.1 e python-dotenv==1.0.0 declarados mas não usados no código)
Domain:        Task Manager API — tasks, users, categories, relatórios de produtividade
Architecture:  Parcialmente organizada — já possui models/, routes/, services/ e utils/ separados, mas as rotas concentram validação e regras de negócio (sem camada controller/service real usada), não há config/ para segredos/ambiente, não há middleware de erro centralizado, e services/notification_service.py e utils/helpers.py contêm código morto (nunca importado pelas rotas)
Source files:  15 files analyzed (app.py, database.py, models/task.py, models/user.py, models/category.py, models/__init__.py, routes/task_routes.py, routes/user_routes.py, routes/report_routes.py, routes/__init__.py, services/notification_service.py, services/__init__.py, utils/helpers.py, utils/__init__.py, seed.py) — ~1160 lines of code
DB tables:     tasks, users, categories
================================

<br/>
<br/>
<br/>

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask
Files:   15 analyzed | ~1160 lines of code

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 4 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials
File: app.py:13
Description: A `SECRET_KEY` do Flask (`'super-secret-key-123'`) está fixada como string literal no código-fonte versionado.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões/cookies assinados; rotacionar o segredo exige novo deploy de código.
Recommendation: Mover para `os.environ["SECRET_KEY"]`, carregado via `.env` (não versionado), conforme playbook P2.

### [CRITICAL] Hardcoded Credentials
File: services/notification_service.py:7-10
Description: Host, usuário e senha de uma conta de e-mail SMTP (`self.email_password = 'senha123'`) estão fixados como literais no construtor de `NotificationService`.
Impact: Exposição da senha real da conta de e-mail da aplicação a qualquer leitor do código-fonte, mesmo sem essa classe estar em uso ativo.
Recommendation: Mover host/usuário/senha para variáveis de ambiente (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`), conforme playbook P2.

### [CRITICAL] Weak/Reversible Password Hashing & Password Hash Exposed in API Responses
File: models/user.py:16-25, 27-32; routes/user_routes.py:86, 129, 207-211
Description: Senhas são "hasheadas" com MD5 sem salt (`hashlib.md5(pwd.encode()).hexdigest()`), um algoritmo quebrado e reversível via rainbow tables/força bruta; além disso, `User.to_dict()` inclui o campo `password` (o hash), que é devolvido nas respostas de `POST /users`, `PUT /users/<id>`, `GET /users`, `GET /users/<id>` e `POST /login`.
Impact: Comprometimento do banco (ou apenas da resposta HTTP) permite recuperar a senha original de qualquer usuário com custo computacional baixo; dados de credenciais vazam publicamente na API.
Recommendation: Substituir MD5 por `werkzeug.security.generate_password_hash`/`check_password_hash` (bcrypt/scrypt) com salt, e remover o campo de senha/hash de qualquer serialização exposta via HTTP, conforme playbook P4.

### [HIGH] Destructive Endpoints Without Authentication/Authorization
File: routes/task_routes.py:225-238 (`DELETE /tasks/<id>`), routes/user_routes.py:134-151 (`DELETE /users/<id>`, que também apaga em cascata as tasks do usuário), routes/report_routes.py:211-223 (`DELETE /categories/<id>`)
Description: Nenhuma rota de exclusão (nem nenhuma outra rota da API) verifica autenticação/autorização antes de executar a operação; o `/login` retorna um token fake (`'fake-jwt-token-' + str(user.id)`, user_routes.py:210) que nenhum endpoint valida.
Impact: Qualquer cliente não autenticado pode apagar tarefas, usuários (com cascata) ou categorias de produção.
Recommendation: Implementar autenticação real (JWT assinado) e um decorator/middleware `requer_autenticacao` aplicado a todas as rotas mutáveis, especialmente `DELETE`, conforme playbook P6.

### [HIGH] Business Logic Inside Route Handlers
File: routes/task_routes.py:85-223 (`create_task`, `update_task`), routes/user_routes.py:42-132 (`create_user`, `update_user`)
Description: Validação de regras de negócio (tamanho de título, status/prioridade/role válidos, formato de e-mail, formato de data) está implementada diretamente nos handlers de rota, em vez de delegada a uma camada de serviço/validação — mesmo já existindo `utils/helpers.py::process_task_data` com essa lógica extraída, porém nunca chamada por nenhuma rota.
Impact: Handlers difíceis de testar isoladamente, duplicação de regras entre criação/atualização, e código morto que diverge do comportamento real ao longo do tempo.
Recommendation: Extrair a validação para uma camada de serviço (`services/task_service.py`, `services/user_service.py`) chamada pelos controllers, reaproveitando/corrigindo `process_task_data` em vez de mantê-lo desconectado, conforme playbook P8.

### [MEDIUM] Query N+1
File: routes/task_routes.py:41-57
Description: Dentro do loop que monta a listagem de `GET /tasks`, o código executa `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` a cada iteração, em vez de usar `JOIN`/eager loading.
Impact: Uma listagem com N tasks gera até `1 + 2N` queries ao banco, degradando performance à medida que o volume de dados cresce.
Recommendation: Usar `db.session.query(Task).join(User, isouter=True).join(Category, isouter=True)` (ou `joinedload`) para montar a listagem em uma única consulta, conforme playbook P10.

### [MEDIUM] Duplicated "Overdue" Calculation Logic
File: models/task.py:50-60 (`is_overdue`, nunca chamado), routes/task_routes.py:30-39, 71-80; routes/user_routes.py:171-180; routes/report_routes.py:33-43, 132-135
Description: A mesma cadeia de `if due_date < utcnow() and status not in (done, cancelled)` é reescrita manualmente em 5 lugares diferentes, apesar de já existir `Task.is_overdue()` pronto para reuso.
Impact: Qualquer mudança na regra de "atrasada" (ex.: novo status terminal) exige editar 5+ pontos, com alto risco de inconsistência entre endpoints.
Recommendation: Remover as duplicatas e chamar `task.is_overdue()` em todos os pontos, conforme playbook P11.

### [MEDIUM] Duplicated Hardcoded Validation Lists
File: models/task.py:39 (`validate_status`, não usado), routes/task_routes.py:110, 177; routes/user_routes.py:71, 120; utils/helpers.py:75, 110 (`VALID_STATUSES`, não usado)
Description: A lista de status válidos (`['pending', 'in_progress', 'done', 'cancelled']`) e a de roles válidos (`['user', 'admin', 'manager']`) são redeclaradas como literais em múltiplos arquivos, incluindo uma constante `VALID_STATUSES` em `helpers.py` que nunca é referenciada.
Impact: Adicionar/remover um status ou role exige alterar várias cópias divergentes, com risco real de inconsistência (ex.: uma rota aceitar um status que outra rejeita).
Recommendation: Centralizar em uma única fonte (ex.: `services/task_service.py::VALID_STATUSES`, `services/user_service.py::VALID_ROLES`) importada por models e rotas, conforme playbook P13 (constantes nomeadas centralizadas).

### [MEDIUM] Deprecated API Usage — `datetime.utcnow()`
File: models/task.py:15-16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38 (uso generalizado no projeto)
Description: `datetime.utcnow()` está deprecated desde o Python 3.12 em favor de `datetime.now(timezone.utc)`, pois retorna um datetime "naive" sem timezone, propenso a bugs de comparação.
Impact: Warnings de depreciação em runtimes mais novos hoje; potencial quebra caso o método seja removido em versões futuras do Python.
Recommendation: Substituir todas as ocorrências por `datetime.now(timezone.utc)`, conforme playbook P14.

### [LOW] Use of `print` for Logging
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39, 41
Description: Eventos de aplicação (criação/atualização/exclusão de recursos, erros) são registrados via `print(...)` em vez de um logger configurável.
Impact: Sem níveis de log, formatação estruturada ou destino configurável (arquivo/serviço externo) em produção; erros silenciosos ou ruidosos dependendo do stdout.
Recommendation: Substituir por `logging.getLogger(__name__)` configurado centralmente, conforme playbook P12.

### [LOW] Non-Descriptive Naming
File: routes/task_routes.py:16 (`t`), 268 (`t`); routes/user_routes.py:14 (`u`), 37 (`t`); routes/report_routes.py:24-28 (`p1`..`p5`)
Description: Variáveis de loop e contadores usam nomes de uma letra ou abreviações genéricas (`t`, `u`, `p1`–`p5`) em vez de nomes que comuniquem a entidade/conceito.
Impact: Reduz legibilidade e dificulta manutenção, especialmente em relatórios com múltiplas variáveis de contagem similares.
Recommendation: Renomear para nomes descritivos (`task`, `user`, `priority_1_count`, etc.).

================================
Total: 11 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

<br/>
<br/>
<br/>

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── app.py                          # entry point / composition root: carrega config, registra
│                                    #   error handlers, CORS por env e blueprints
├── database.py                     # instância única do SQLAlchemy (db)
├── seed.py                         # script de seed (fora do runtime HTTP da API)
├── config/
│   ├── settings.py                 # SECRET_KEY, DATABASE_URL, ALLOWED_ORIGINS, SMTP_*,
│   │                                #   JWT_EXPIRATION_SECONDS — tudo vindo de os.environ/.env
│   └── logging_config.py           # configuração central de logging estruturado
├── middlewares/
│   ├── auth.py                     # requer_autenticacao(papel=None): gera/valida JWT real
│   │                                #   (substitui o token fake do login)
│   └── error_handler.py            # tratamento de erro centralizado (HTTPException + Exception),
│                                    #   formato consistente {"error":..., "success": false}
├── models/
│   ├── task.py                     # TASK_STATUSES, is_overdue()/to_dict() como fonte única de
│   │                                #   verdade (elimina duplicação em 5 lugares)
│   ├── user.py                     # USER_ROLES, senha com werkzeug generate/check_password_hash,
│   │                                #   to_dict() nunca inclui password/hash
│   └── category.py
├── services/
│   ├── task_service.py             # validação de payload, create/update, busca, stats e
│   │                                #   list_tasks_with_relations() (JOIN único, corrige N+1)
│   ├── user_service.py             # validação de payload, create/update, authenticate()
│   └── notification_service.py     # credenciais SMTP via config/settings, logging em vez de print
├── controllers/
│   ├── task_controller.py
│   ├── user_controller.py          # login gera JWT real via middlewares/auth.generate_token
│   └── report_controller.py        # relatórios + CRUD de categorias
├── routes/
│   ├── task_routes.py              # mapeamento HTTP puro; DELETE /tasks/<id> protegido por
│   │                                #   requer_autenticacao()
│   ├── user_routes.py              # DELETE /users/<id> protegido por requer_autenticacao()
│   └── report_routes.py            # DELETE /categories/<id> protegido por requer_autenticacao()
├── utils/helpers.py                # apenas helpers genéricos reutilizados (format_date,
│                                    #   calculate_percentage, parse_date, is_valid_color, ...)
├── .env.example                    # template de variáveis de ambiente (SECRET_KEY, SMTP_*, ...)
├── .gitignore                      # adicionado: .env, *.db, __pycache__, .venv
└── requirements.txt                # + pyjwt==2.9.0

## Validation
  ✓ Application boots without errors (uv + venv Python 3.12, `python app.py`)
  ✓ All endpoints respond correctly (smoke-tested via curl: /health, /, /tasks CRUD + search +
    stats, /users CRUD + /users/<id>/tasks, /login, /reports/summary, /reports/user/<id>,
    /categories CRUD)
  ✓ Zero anti-patterns remaining (grep confirms no `print()` in app code, no MD5/hashlib password
    hashing, no hardcoded secrets, no `datetime.utcnow()` calls outside comments)

## Documented behavior changes (security fixes — required by C1–C4/H2 findings)
- `/login` now returns a real signed JWT (`Authorization: Bearer <token>`) instead of the fake
  `'fake-jwt-token-' + id` string; existing clients must send this token to destructive endpoints.
- `DELETE /tasks/<id>`, `DELETE /users/<id>` and `DELETE /categories/<id>` now require a valid JWT
  (`Authorization: Bearer <token>`) — previously these were open to any unauthenticated caller.
- `User.to_dict()` no longer includes the password/password hash field in any API response
  (`GET/POST/PUT /users`, `POST /login`).
- Passwords are now hashed with `werkzeug.security.generate_password_hash` (salted) instead of
  unsalted MD5; existing seeded passwords are re-hashed by `seed.py`.
- CORS is now restricted via `ALLOWED_ORIGINS` (empty/deny-by-default outside `FLASK_ENV=development`)
  instead of the previous fully-open `CORS(app)`.
- `SECRET_KEY` and SMTP credentials must now be provided via environment variables (see
  `.env.example`); the app refuses to start in non-development mode without `SECRET_KEY` set.
================================
