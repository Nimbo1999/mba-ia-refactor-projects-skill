================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express ^4.18.2
Dependencies:  express (web framework), sqlite3 (embedded SQL database, no ORM)
Domain:        LMS (plataforma de cursos) com fluxo de checkout — usuários, cursos, matrículas (enrollments), pagamentos
Architecture:  Monolítica — tudo em 3 arquivos (app.js, AppManager.js, utils.js), sem separação de camadas (roteamento, regras de negócio e acesso a dados misturados em uma única classe "God Object")
Source files:  3 files analyzed (app.js, AppManager.js, utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs
================================

<br/>
<br/>
<br/>

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials
File: src/utils.js:1-6
Description: Credenciais de banco de dados (dbUser, dbPass), a chave de gateway de pagamento (paymentGatewayKey) e o usuário SMTP estão gravados como literais de string diretamente no código-fonte versionado.
Impact: Qualquer pessoa com acesso ao repositório (incluindo histórico de git) obtém acesso a credenciais de produção reais, permitindo comprometer banco de dados e gateway de pagamento.
Recommendation: Mover todos os segredos para variáveis de ambiente (`process.env.DB_PASS`, etc.), carregadas via `.env`/cofre de segredos, e nunca commitar o `.env` real.

### [CRITICAL] Weak / Fake Password Hashing
File: src/utils.js:17-23, src/AppManager.js:68
Description: A função `badCrypto` "hasheia" a senha concatenando repetidamente uma codificação Base64 truncada — um algoritmo reversível e sem salt, não um hash criptográfico unidirecional real.
Impact: Senhas de usuários podem ser recuperadas/quebradas trivialmente em caso de vazamento do banco, expondo credenciais reais dos usuários (inclusive reuso em outros sistemas).
Recommendation: Substituir `badCrypto` por `bcrypt`/`argon2` com salt, usando `bcrypt.hash`/`bcrypt.compare` para gravação e verificação de senha.

### [CRITICAL] Unauthenticated Admin Endpoint Exposing Sensitive Data
File: src/AppManager.js:80-129
Description: A rota `GET /api/admin/financial-report` retorna nomes, e-mails, valores pagos e receita de todos os cursos e usuários sem nenhuma verificação de autenticação/autorização antes do handler.
Impact: Qualquer cliente não autenticado pode extrair dados financeiros e pessoais completos da plataforma, configurando um vazamento grave de dados sensíveis.
Recommendation: Adicionar middleware de autenticação + verificação de papel (role) de administrador antes do handler, seguindo o padrão de composition root descrito no playbook (seção de middlewares de autenticação).

### [HIGH] God Class / God Module
File: src/AppManager.js:1-141
Description: A classe `AppManager` concentra inicialização de banco, definição de schema, seeds, roteamento HTTP, regras de negócio de checkout e o relatório financeiro para 5 entidades distintas (users, courses, enrollments, payments, audit_logs) em um único arquivo/classe.
Impact: Dificulta extremamente manutenção, testes unitários isolados e a compreensão do fluxo de cada domínio; qualquer mudança tem alto risco de efeito colateral em outra funcionalidade.
Recommendation: Separar em camadas MVC — `models/` por entidade, `controllers/` por rota, `services/` para as regras de negócio (checkout, relatório), conforme `04-architecture-guidelines.md`.

### [HIGH] Endpoint destrutivo sem autenticação/autorização
File: src/AppManager.js:131-137
Description: A rota `DELETE /api/users/:id` apaga um usuário diretamente a partir do parâmetro da URL, sem nenhuma checagem de autenticação/autorização, e a própria resposta admite que matrículas e pagamentos ficam "sujos" (órfãos) no banco.
Impact: Qualquer cliente pode apagar contas de usuários em produção e corromper a integridade referencial do banco (dados órfãos em `enrollments`/`payments`).
Recommendation: Exigir autenticação + autorização de administrador antes do handler e, na camada de serviço, tratar a exclusão em cascata (ou soft delete) das entidades relacionadas.

### [HIGH] Lógica de negócio dentro de Controllers/Routes
File: src/AppManager.js:28-78
Description: O handler da rota `POST /api/checkout` implementa diretamente toda a regra de negócio: criação de usuário, decisão de aprovação/recusa de pagamento (`cc.startsWith("4")`), matrícula, registro de pagamento e log de auditoria, tudo aninhado em callbacks dentro do próprio handler.
Impact: Regra de negócio não é reutilizável nem testável isoladamente da camada HTTP; qualquer alteração no fluxo de checkout exige mexer no controller inteiro, aumentando risco de regressão.
Recommendation: Extrair a lógica para um `CheckoutService`/`PaymentService` dedicado, deixando o controller responsável apenas por receber a requisição, chamar o serviço e formatar a resposta.

### [HIGH] Estado global mutável / forte acoplamento sem injeção de dependência
File: src/utils.js:9-15, src/AppManager.js:59
Description: `globalCache` e `totalRevenue` são variáveis mutáveis no escopo do módulo, atualizadas por `logAndCache` e referenciadas por múltiplos pontos do código sem nenhuma abstração de container/factory.
Impact: Cria acoplamento oculto entre módulos, dificulta testes (estado compartilhado entre execuções) e abre espaço para condições de corrida em cenários concorrentes.
Recommendation: Substituir por um serviço de cache injetado explicitamente (ou `app.locals`/container de DI), eliminando variáveis globais mutáveis.

### [MEDIUM] Query N+1
File: src/AppManager.js:89-127
Description: O relatório financeiro executa, para cada curso, uma query de matrículas, e para cada matrícula duas queries adicionais (usuário e pagamento) dentro de laços aninhados (`forEach` dentro de `forEach`).
Impact: Para N cursos e M matrículas, o número de queries cresce proporcionalmente a N×M, degradando performance de forma significativa à medida que a base cresce.
Recommendation: Substituir por uma única consulta com `JOIN` entre `courses`, `enrollments`, `users` e `payments` (ou agregação no nível do banco), conforme playbook de eliminação de N+1.

### [MEDIUM] Ausência de validação de entrada em rotas
File: src/AppManager.js:29-35
Description: O handler de checkout apenas verifica presença (`!u`, `!e`, `!cid`, `!cc`) mas não valida tipo, formato de e-mail, formato do número de cartão nem tamanho/força da senha antes de usar os valores em lógica de negócio e persistência.
Impact: Dados malformados podem ser persistidos no banco (e-mails inválidos, cartões com formato incorreto), e cálculos/decisões de negócio podem falhar silenciosamente ou de forma inesperada.
Recommendation: Adicionar uma camada de validação de schema (ex.: `zod`/`joi`/validação manual explícita) antes de qualquer regra de negócio, rejeitando requisições malformadas com erro 400 detalhado.

### [LOW] Uso de console.log para logging
File: src/app.js:13, src/AppManager.js:45, src/utils.js:13
Description: Mensagens de diagnóstico (inicialização do servidor, processamento de cartão, cache) são emitidas via `console.log` em vez de um logger estruturado configurável.
Impact: Dificulta correlacionar logs por nível/severidade em produção e não permite redirecionar/filtrar saída sem alterar código-fonte.
Recommendation: Adotar um módulo de logging (ex.: `pino`/`winston`) com níveis (`info`, `warn`, `error`) e formato estruturado.

### [LOW] Nomenclatura pouco descritiva
File: src/AppManager.js:29-33
Description: As variáveis do corpo da requisição de checkout são nomeadas de forma abreviada e pouco descritiva (`u`, `e`, `p`, `cid`, `cc`), exigindo esforço extra para entender o que cada uma representa.
Impact: Reduz legibilidade e aumenta a chance de erros ao dar manutenção no fluxo de checkout.
Recommendation: Renomear para nomes descritivos (`username`, `email`, `password`, `courseId`, `cardNumber`).

================================
Total: 11 findings
================================

<br/>
<br/>
<br/>

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
src/
├── app.js                              # composition root (DI, migrate/seed, listen)
├── config/
│   ├── env.js                          # todas as configs vêm de process.env / .env
│   └── logger.js                       # logger estruturado (substitui console.log)
├── db/
│   ├── connection.js                   # conexão sqlite injetável, promisificada
│   └── schema.js                       # CREATE TABLE + seeds
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   ├── enrollmentModel.js              # inclui query única (JOIN) do relatório financeiro
│   ├── paymentModel.js
│   └── auditLogModel.js
├── services/
│   ├── passwordService.js              # hash real (bcrypt), substitui badCrypto
│   ├── cacheService.js                 # substitui globalCache/totalRevenue mutáveis
│   ├── checkoutService.js              # regra de negócio extraída do controller
│   ├── financialReportService.js       # agregação em memória, sem N+1
│   └── userService.js                  # delete em cascata (sem dados órfãos)
├── controllers/
│   ├── checkoutController.js
│   ├── financialReportController.js
│   └── userController.js
├── middlewares/
│   ├── authMiddleware.js               # requireAdmin (Bearer token)
│   └── errorHandler.js                 # tratamento de erro centralizado
└── routes/
    ├── checkoutRoutes.js
    ├── adminRoutes.js
    └── userRoutes.js
.env                                    # (novo)
.env.example                            # (novo)
.gitignore                              # (novo)
```

## Validation
  ✓ Application boots without errors (`node src/app.js`)
  ✓ All endpoints respond correctly (checkout aprovado/recusado/bad-request, financial-report,
    delete user — testados via curl)
  ✓ Zero anti-patterns remaining
================================
