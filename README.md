# Refatoração Arquitetural Automatizada com Custom Skills

Este repositório é a entrega do desafio **"Criação de Skills — Refatoração Arquitetural
Automatizada"**: uma Custom Skill (`refactor-arch`) capaz de analisar, auditar e refatorar
qualquer backend legado para o padrão MVC, de forma agnóstica de linguagem/framework.

A skill foi construída e executada com **Claude Code**, e validada nos 3 projetos fornecidos:

| # | Projeto | Stack | Nível de organização inicial |
|---|---|---|---|
| 1 | [`code-smells-project/`](/code-smells-project) | Python/Flask | Monolítico, sem separação de camadas |
| 2 | [`ecommerce-api-legacy/`](/ecommerce-api-legacy) | Node.js/Express | Monolítico ("God Class" `AppManager`) |
| 3 | [`task-manager-api/`](/task-manager-api) | Python/Flask + SQLAlchemy | Parcialmente organizado (`models/`, `routes/`, `services/`) mas com problemas de segurança/qualidade |

> Nota sobre a ferramenta: a skill reside canonicamente em `.agents/skills/refactor-arch/` dentro de
> cada projeto (por preferência pessoal de organização), com um **symlink**
> `.claude/skills/refactor-arch -> ../../.agents/skills/refactor-arch` em cada um deles, para que o
> Claude Code a descubra normalmente via `/refactor-arch`. Conteúdo e comportamento são idênticos ao
> exigido pela convenção `.claude/skills/` do desafio — apenas a localização física do arquivo-fonte
> muda.

## Índice

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Referências](#referências)

---

## A) Análise Manual

Abaixo estão os achados por projeto, com severidade (CRITICAL,HIGH,MEDIUM,LOW) e justificativa de relevância.

### Projeto 1 — `code-smells-project/` (Python/Flask)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| **CRITICAL** | SQL Injection — praticamente toda query é montada concatenando strings com valores de request (`id`, `email`, `senha`, termo de busca) | `models.py` (quase todas as funções de acesso a dados) | Permite leitura/alteração/exclusão arbitrária de qualquer tabela do banco a partir de qualquer input do usuário — compromete a aplicação inteira. |
| **CRITICAL** | Endpoint `/admin/query` executa SQL arbitrário vindo do corpo da requisição, sem autenticação | `app.py:59-78` | Um atacante não autenticado pode rodar `DROP TABLE`, extrair a tabela de usuários/senhas ou qualquer outra operação destrutiva. |
| **CRITICAL** | `SECRET_KEY` do Flask hardcoded e reexposta em texto puro na resposta do `/health` | `app.py:8`, `controllers.py` (`health_check`) | Vaza a chave de assinatura de sessão para qualquer chamador — permite forjar sessões/tokens da aplicação. |
| **CRITICAL** | Senhas gravadas e comparadas em texto puro (sem hash) | `models.py` (`criar_usuario`, `login_usuario`) | Um vazamento do banco expõe as senhas reais de todos os usuários, com alto risco de reuso em outros sistemas. |
| **HIGH** | `/admin/reset-db` apaga todas as tabelas sem exigir nenhuma credencial | `app.py:47-57` | Qualquer requisição não autenticada destrói a base de produção por completo. |
| **HIGH** | God Module — `models.py`/`controllers.py` concentram 4 domínios de negócio (produtos, usuários, pedidos, relatórios) num único arquivo cada | `models.py`, `controllers.py` | Qualquer mudança em uma entidade arrisca efeito colateral nas demais; impossível testar em isolamento. |
| **MEDIUM** | Query N+1 ao montar itens de pedido (um `SELECT` por item dentro de um loop) | `models.py` (`get_pedidos_usuario`, `get_todos_pedidos`) | Degrada performance de forma proporcional ao volume de pedidos/itens. |
| **MEDIUM** | Serialização de produto/pedido reescrita de forma idêntica em várias funções | `models.py` | Qualquer mudança de schema exige atualizar múltiplas funções manualmente, com risco de inconsistência. |
| **LOW** | Uso de `print()` para logging de eventos/erros | `app.py`, `controllers.py` | Sem níveis, formato ou destino configurável — dificulta observabilidade em produção. |
| **LOW** | "Magic numbers" nas faixas de desconto (`10000`, `5000`, `1000`, `0.1`, `0.05`) | `models.py` (`relatorio_vendas`) | Reduz legibilidade e dificulta ajustar as regras de negócio de forma consistente. |

### Projeto 2 — `ecommerce-api-legacy/` (Node.js/Express)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| **CRITICAL** | Credenciais de banco, chave do gateway de pagamento e usuário SMTP hardcoded | `src/utils.js:1-6` | Qualquer pessoa com acesso ao repositório (inclusive histórico de git) obtém credenciais de produção reais. |
| **CRITICAL** | `badCrypto` "hasheia" senha concatenando Base64 truncado — reversível, sem salt | `src/utils.js:17-23` | Não é um hash criptográfico real; senhas podem ser recuperadas trivialmente em caso de vazamento. |
| **CRITICAL** | `GET /api/admin/financial-report` expõe dados financeiros e pessoais de todos os usuários, sem autenticação | `src/AppManager.js:80-129` | Vazamento grave de dados sensíveis (PII + receita) acessível a qualquer cliente não autenticado. |
| **HIGH** | God Class — `AppManager` concentra schema, seeds, roteamento, regra de negócio de checkout e relatório para 5 entidades | `src/AppManager.js:1-141` | Alto risco de efeito colateral em qualquer mudança; impossível testar unidades isoladamente. |
| **HIGH** | `DELETE /api/users/:id` remove usuário sem autenticação, deixando matrículas/pagamentos órfãos | `src/AppManager.js:131-137` | Qualquer cliente pode apagar contas em produção e corromper a integridade referencial do banco. |
| **MEDIUM** | Relatório financeiro executa N×M queries aninhadas (uma por matrícula, duas por pagamento) | `src/AppManager.js:89-127` | Degrada performance de forma acentuada à medida que a base de cursos/matrículas cresce. |
| **MEDIUM** | Checkout só valida presença dos campos, não formato (e-mail, cartão) | `src/AppManager.js:29-35` | Permite persistir dados malformados e mascara erros de negócio. |
| **LOW** | `console.log` usado como logging de aplicação | `src/app.js`, `src/AppManager.js`, `src/utils.js` | Sem níveis/formatação estruturada, dificultando correlação de logs em produção. |
| **LOW** | Nomes de variável abreviados no checkout (`u`, `e`, `p`, `cid`, `cc`) | `src/AppManager.js:29-33` | Reduz legibilidade e aumenta risco de erro na manutenção do fluxo de pagamento. |

### Projeto 3 — `task-manager-api/` (Python/Flask, parcialmente organizado)

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| **CRITICAL** | Senhas com MD5 sem salt, e o hash é devolvido nas respostas HTTP (`to_dict()`) | `models/user.py:16-32`, `routes/user_routes.py` | MD5 é quebrável por força bruta/rainbow table; pior ainda, o hash vaza publicamente em `GET/POST/PUT /users` e `/login`. |
| **CRITICAL** | `SECRET_KEY` e credenciais SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | Segredos versionados no repositório, incluindo senha de uma conta de e-mail real. |
| **HIGH** | Nenhuma rota (incluindo `DELETE`) valida autenticação — `/login` devolve um token fake que nada verifica | `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` | Qualquer cliente não autenticado apaga tasks, usuários (com cascata) ou categorias de produção. |
| **HIGH** | Validação de negócio duplicada dentro dos handlers de rota, apesar de já existir `process_task_data` pronta (porém nunca chamada) | `routes/task_routes.py`, `routes/user_routes.py`, `utils/helpers.py` | Handlers difíceis de testar isoladamente; existe até código morto que diverge do comportamento real ao longo do tempo — um risco arquitetural sutil, mesmo o projeto já tendo pastas separadas. |
| **MEDIUM** | Query N+1 ao listar tasks (`User.query.get`/`Category.query.get` dentro do loop) | `routes/task_routes.py:41-57` | Uma listagem com N tasks gera até `1 + 2N` queries, degradando performance conforme o volume cresce. |
| **MEDIUM** | Cálculo de "atrasada" (`is_overdue`) reescrito manualmente em 5 lugares, apesar de já existir no model | `models/task.py`, `routes/*.py` | Qualquer mudança na regra de "atrasada" exige editar 5+ pontos, com alto risco de inconsistência. |
| **MEDIUM** | `datetime.utcnow()` usado em todo o projeto — API deprecated desde Python 3.12 | Uso disperso em `models/`, `routes/`, `services/` | Gera datetimes "naive" propensos a bugs de comparação e warnings/quebras em runtimes futuros. |
| **LOW** | `print()` para eventos de aplicação/erros | `routes/*.py`, `services/notification_service.py` | Sem logging estruturado, dificultando observabilidade. |
| **LOW** | Nomes de variável de uma letra (`t`, `u`, `p1`..`p5`) | `routes/task_routes.py`, `routes/report_routes.py` | Reduz legibilidade, especialmente em relatórios com múltiplas variáveis de contagem similares. |

> O projeto 3 mostra bem por que "já ter pastas separadas" não é sinônimo de arquitetura correta: a
> separação física existe (`models/`, `routes/`, `services/`), mas a regra de negócio real ainda mora
> nas rotas, há código morto desconectado do fluxo, e problemas clássicos de segurança (MD5, sem
> auth) persistem — exatamente o cenário que a skill precisa saber diferenciar de um monólito puro.

---

## B) Construção da Skill

### Decisões de design — SKILL.md e arquivos de referência

O `SKILL.md` foi escrito como **orquestrador fino**: ele descreve a sequência das 3 fases, as regras
gerais (o que ignorar ao escanear, formato de saída determinístico, nunca inventar números) e, em
cada fase, aponta explicitamente para o arquivo de referência que contém o conhecimento de domínio
necessário. Isso mantém o "prompt" curto e fácil de auditar, e separa claramente **orquestração**
(`SKILL.md`) de **conhecimento** (`reference/*.md`):

```
.agents/skills/refactor-arch/
├── SKILL.md                          # as 3 fases, regras gerais, formatos de saída exatos
└── reference/
    ├── 01-project-analysis.md        # heurísticas de detecção de stack/BD/domínio/arquitetura
    ├── 02-anti-patterns-catalog.md   # catálogo de anti-patterns com sinais de detecção + severidade
    ├── 03-report-template.md         # template exato do relatório de auditoria (Fase 2)
    ├── 04-architecture-guidelines.md # regras do MVC alvo e responsabilidade de cada camada
    └── 05-refactoring-playbook.md    # transformações antes/depois, 1:1 com o catálogo
```

Cada arquivo de referência cobre exatamente uma das 5 áreas de conhecimento exigidas pelo desafio, e
o `SKILL.md` faz link direto (`[reference/02-...](./reference/02-...)`) para cada um no passo da fase
correspondente — evitando que o agente precise "adivinhar" qual arquivo ler em qual momento.

Outras decisões importantes:

- **Formatos de saída fixos no `SKILL.md`** (blocos `PHASE 1`, `ARCHITECTURE AUDIT REPORT`,
  `PHASE 3`) — isso é o que garante saída comparável entre os 3 projetos e execuções, em vez de o
  agente reformatar livremente a cada rodada.
- **Fases estritamente sequenciais e com trava explícita**: o `SKILL.md` instrui literalmente "nunca
  pule a confirmação da Fase 2 para ir direto à Fase 3, mesmo que o usuário peça 'refatore tudo'".
  Isso veio de um risco concreto observado durante os testes: LLMs tendem a "otimizar" e pular
  confirmações quando o pedido do usuário parece urgente.
- **Regra explícita de não inventar números** (findings, linhas, contagem de arquivos) — evita que a
  Fase 2 gere um relatório "bonito" mas fabricado quando o código real tem menos problemas do que o
  esperado.
- **Regra de migração incremental** para projetos que já têm alguma separação de camadas (ver
  `04-architecture-guidelines.md`, seção 4): a Fase 3 deve *evoluir* a estrutura existente em vez de
  recriá-la do zero — decisão tomada diretamente por causa do projeto 3 (`task-manager-api`), que já
  tinha `models/`, `routes/`, `services/`.

### Anti-patterns incluídos no catálogo e por quê

O catálogo (`02-anti-patterns-catalog.md`) tem **14 anti-patterns nomeados** distribuídos nas 4 severidades, mais uma seção dedicada a **APIs deprecated**:

| Severidade | Anti-patterns | Motivo de inclusão |
|---|---|---|
| CRITICAL | SQL Injection, Credenciais hardcoded, Endpoint admin executa SQL/código arbitrário sem auth, Senhas em texto puro | Correspondem 1:1 aos 4 exemplos de CRITICAL do próprio enunciado e foram os primeiros problemas encontrados em **todos os 3 projetos** na análise manual |
| HIGH | God Class/Module, Endpoint destrutivo sem auth, Configuração insegura de produção, Lógica de negócio em Controllers, Estado global mutável/sem DI | Cobrem as violações de MVC/SOLID citadas no enunciado e mais dois padrões recorrentes observados na análise manual. |
| MEDIUM | Query N+1, Duplicação de lógica de serialização, Ausência de validação de entrada, Listas de validação duplicadas/hardcoded | Bate diretamente com os exemplos do enunciado e com a duplicação de regras observada em `task-manager-api`. |
| LOW | `print`/`console.log` para logging, Magic numbers, Nomenclatura pouco descritiva | Presentes nos 3 projetos de forma consistente e citados como exemplo de LOW no enunciado. |
| — (transversal) | **APIs/padrões deprecated** | Exigência explícita do desafio. Escrita como seção à parte porque sua severidade **depende do contexto** — isso permitiu detectar `datetime.utcnow()` no projeto 3 sem forçar uma categoria fixa. |

Cada anti-pattern segue o mesmo formato: **Conceito** → **Sinais de detecção** → **Exemplos ilustrativos**. Isso foi
proposital: "sinais de detecção" vagos como "código ruim" não são acionáveis por um agente.

Algo como "palavra-chave SQL na mesma expressão que um operador de concatenação envolvendo uma variável, sem placeholder na chamada de execução" é.

### Como garantimos que a skill é agnóstica de tecnologia

1. **Conceito antes de exemplo, sempre.** Todo item de `01-project-analysis.md`,
   `02-anti-patterns-catalog.md` e `05-refactoring-playbook.md` descreve primeiro o *conceito
   estrutural* (ex.: "string concatenada formando SQL"), e só depois traz exemplos em algumas linguagens como ilustração — nunca como a única forma reconhecida. Isso é reforçado
   explicitamente logo no topo de cada arquivo de referência e no princípio central do `SKILL.md`.
2. **Nenhum literal de projeto específico dentro da skill.** Nada em `SKILL.md`/`reference/*.md`
   menciona `app.py`, `produtos`, `AppManager.js` ou qualquer nome específico dos 3 projetos-alvo —
   apenas sinais genéricos ("arquivo de manifest de dependências", "pasta chamada
   `models`/`controllers`/`routes`", "cursor aberto dentro de um loop").
3. **Detecção de linguagem/framework por manifest + padrões de import**, não por extensão isolada:
   `01-project-analysis.md` tem uma tabela de manifests (`requirements.txt`, `package.json`,
   `pom.xml`, `Gemfile`, `go.mod`, `*.csproj`) e uma segunda camada de sinais no próprio código-fonte
   (`from flask import Flask`, `require('express')`) como fallback, cobrindo Python, Node, Java, Ruby,
   Go e C# mesmo sem termos projetos de teste nessas 2 últimas stacks.
4. **Migração incremental em vez de "sempre recriar do zero"**: a Fase 3 lê o que a Fase 1 já
   detectou sobre camadas existentes e evolui a estrutura, em vez de assumir sempre um monólito —
   validado concretamente ao rodar a skill, sem editar seu conteúdo, no `task-manager-api` logo após validá-la no `code-smells-project`.
5. **Teste de aceitação de agnosticismo definido desde o início do planejamento** (ver
   [`docs/refactor-arch-skill-requirements.md`](/docs/refactor-arch-skill-requirements.md)): a skill
   só foi considerada "pronta" quando pôde ser **copiada, sem nenhuma edição de conteúdo**, do
   `code-smells-project` para os outros 2 projetos e produzir resultados corretos nos 3 — se algum
   ajuste fosse necessário para funcionar em outro projeto, isso seria sinal de acoplamento indevido
   ao projeto 1, e a correção deveria generalizar a regra, nunca criar um caso especial.

### Desafios encontrados e como foram resolvidos

- **Risco de pular a confirmação da Fase 2.** Em pedidos como "refatore o projeto", o agente tende a
  tentar ser útil e ir direto à ação. Resolvido explicitando no `SKILL.md`, em letras maiúsculas de
  ênfase, que a Fase 2 **sempre** pausa e pergunta, independente de como o usuário formule o pedido.
- **Findings "genéricos demais" na primeira versão do catálogo.** Uma primeira tentativa descrevia
  anti-patterns em linguagem mais abstrata (ex.: "acoplamento ruim"), o que gerava relatórios vagos
  sem arquivo/linha precisos. Resolvido reescrevendo cada entrada do catálogo com uma seção **Sinais
  de detecção** concreta e verificável no código (regex/padrão estrutural), seguindo a dica do próprio
  enunciado ("query SQL dentro de loop for" é acionável, "código ruim" não é).
- **Projetos com organização parcial confundindo a heurística de arquitetura.** A primeira versão da
  heurística de Fase 1 classificava qualquer projeto com pastas (`models/`, `routes/`) como "bem
  organizado", o que mascarava os problemas reais do `task-manager-api`. Resolvido separando explicitamente "presença de camadas nomeadas"
  de "responsabilidade correta de cada camada" (comportamento) em `01-project-analysis.md`, e
  reforçando em `04-architecture-guidelines.md` que a Fase 3 deve auditar responsabilidade, não só
  nomenclatura de pasta.
- **Severidade variável de "API deprecated".** Como a mesma API deprecated pode ser puramente
  cosmética (`Buffer` antigo) ou também um problema de segurança, uma regra fixa de severidade geraria
  classificações erradas. Resolvido com uma regra condicional na seção de deprecated do catálogo:
  MEDIUM por padrão, LOW se cosmético, ou a severidade do problema de segurança correspondente quando
  aplicável.
- **Validar "aplicação funciona" de forma agnóstica de stack.** Comandos de boot e teste de endpoint
  são diferentes em Python e Node. Resolvido deixando o comando "idiomático da stack detectada na Fase
  1" (`python app.py`/`flask run` vs. `node src/app.js`) como parâmetro da instrução de validação da
  Fase 3, em vez de fixar um comando único no `SKILL.md`.

---

## C) Resultados

### Resumo dos relatórios de auditoria (Fase 2)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total de findings |
|---|---|---|---|---|---|
| 1 — `code-smells-project` | 4 | 5 | 3 | 3 | **15** |
| 2 — `ecommerce-api-legacy` | 3 | 4 | 2 | 2 | **11** |
| 3 — `task-manager-api` | 3 | 2 | 4 | 2 | **11** |

Relatórios completos (saída literal da Fase 2, incluindo Fase 1 e Fase 3 anexadas para contexto):
[`reports/audit-project-1.md`](/reports/audit-project-1.md),
[`reports/audit-project-2.md`](/reports/audit-project-2.md),
[`reports/audit-project-3.md`](/reports/audit-project-3.md).

Os 3 projetos ultrapassam com folga o mínimo de 5 findings e todos incluem múltiplos CRITICAL/HIGH,
batendo com o gabarito levantado na análise manual da seção A.

### Comparação antes/depois da estrutura

**Projeto 1 — `code-smells-project`**

| Antes | Depois |
|---|---|
| `app.py` (rotas + 2 endpoints admin com lógica embutida) | `app.py` — apenas entry point / composition root (`create_app`, CORS, blueprints) |
| `controllers.py` (God Module: validação + orquestração de 4 domínios) | `config/settings.py`, `models/{produto,usuario,pedido}_model.py`, `services/{produto,usuario,pedido,relatorio,notificacao}_service.py`, `controllers/*_controller.py`, `routes/*_routes.py` |
| `models.py` (SQL cru concatenado, N+1, serialização duplicada) | Queries parametrizadas + `JOIN` (elimina N+1) + serializers únicos por entidade |
| `database.py` (conexão global mutável) | `models/connection.py` — conexão por-request via `flask.g` |
| Sem `config/`, sem middleware de erro, sem `.env` | `config/settings.py` (lê `os.environ`), `middlewares/auth.py` + `middlewares/error_handler.py`, `.env`/`.env.example` |

**Projeto 2 — `ecommerce-api-legacy`**

| Antes | Depois |
|---|---|
| `src/AppManager.js` (God Class: schema + seeds + rotas + regra de negócio + relatório) | `db/schema.js`, `models/{user,course,enrollment,payment,auditLog}Model.js`, `services/{checkout,financialReport,user,password,cache}Service.js`, `controllers/*Controller.js`, `routes/*Routes.js` |
| `src/utils.js` (credenciais hardcoded, `badCrypto`, cache global mutável) | `config/env.js` (segredos via `process.env`), `services/passwordService.js` (bcrypt real), `services/cacheService.js` (encapsulado) |
| Sem middleware de auth/erro, sem `.env` | `middlewares/authMiddleware.js` (protege `/admin/*` e `DELETE /users/:id`), `middlewares/errorHandler.js`, `.env`/`.env.example` |
| Relatório financeiro com N×M queries aninhadas | `financialReportService.js` com consulta agregada, sem N+1 |

**Projeto 3 — `task-manager-api`**

| Antes | Depois |
|---|---|
| `models/`, `routes/`, `services/` já existiam, mas regra de negócio ficava nas rotas | `services/task_service.py`/`user_service.py` concentram validação e regra de negócio real; rotas viram mapeamento HTTP puro |
| `SECRET_KEY`/SMTP hardcoded, sem `config/` | `config/settings.py` (tudo via `os.environ`/`.env`), `config/logging_config.py` |
| Senha em MD5 sem salt, exposta em `to_dict()` | `werkzeug.security.generate_password_hash`/`check_password_hash`; `to_dict()` nunca inclui senha/hash |
| `/login` devolve token fake que nada valida; nenhuma rota exige auth | `middlewares/auth.py` gera/valida JWT real; `DELETE /tasks|users|categories/<id>` exigem `Authorization: Bearer <token>` |
| `is_overdue`/`VALID_STATUSES` existiam mas nunca eram usados (código morto duplicado em 5 lugares) | Model é a única fonte de verdade; duplicações removidas |
| Sem middleware de erro centralizado | `middlewares/error_handler.py` — formato de erro consistente |

> Mudanças de comportamento decorrentes de correções de segurança (obrigatórias pelos findings
> CRITICAL/HIGH) foram documentadas explicitamente ao final de cada relatório de Fase 3 — por
> exemplo, `/login` do projeto 3 passou a devolver um JWT real em vez do token fake anterior, e os
> endpoints `DELETE` dos 3 projetos passaram a exigir autenticação.

### Checklist de validação preenchido

**Projeto 1 — `code-smells-project`**

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (E-commerce — produtos, pedidos, usuários)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (15 findings)
- [x] Detecção de APIs deprecated incluída (não aplicável nesta stack/versão — nenhuma encontrada)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente
```

**Projeto 2 — `ecommerce-api-legacy`**

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (JavaScript / Node.js)
- [x] Framework detectado corretamente (Express 4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS com checkout — usuários, cursos, matrículas, pagamentos)
- [x] Número de arquivos analisados condiz com a realidade (3 arquivos)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11 findings)
- [x] Detecção de APIs deprecated incluída (nenhuma encontrada nesta base de código)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente
```

**Projeto 3 — `task-manager-api`**

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0 + Flask-SQLAlchemy 3.1.1)
- [x] Domínio da aplicação descrito corretamente (Task Manager — tasks, users, categories, relatórios)
- [x] Número de arquivos analisados condiz com a realidade (15 arquivos)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11 findings)
- [x] Detecção de APIs deprecated incluída (`datetime.utcnow()`, classificado MEDIUM)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC (evoluída a partir da organização parcial existente)
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados (já existiam; passaram a ser fonte única de verdade)
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente
```

### Logs das aplicações rodando após a refatoração

**Projeto 1 — `code-smells-project`** (`python app.py` + smoke test):

```
2026-08-02 21:49:16 INFO __main__: SERVIDOR INICIADO
2026-08-02 21:49:16 INFO __main__: Rodando em http://0.0.0.0:5000
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000

$ curl -s http://127.0.0.1:5000/health
{"ambiente":"production","counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl -s http://127.0.0.1:5000/produtos
{"dados":[{"ativo":1,"categoria":"informatica","descricao":"Notebook potente para jogos", ...}], ...}
```

**Projeto 2 — `ecommerce-api-legacy`** (`node src/app.js` + smoke test):

```
{"level":"info","message":"LMS API running on port 3000","timestamp":"2026-08-03T00:50:09.590Z"}

$ curl -s -X POST http://127.0.0.1:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"joao","eml":"joao@test.com","pwd":"123456","c_id":1,"card":"4111111111111111"}'
{"msg":"Sucesso","enrollment_id":2}

$ curl -s http://127.0.0.1:3000/api/admin/financial-report -H "Authorization: Bearer <ADMIN_TOKEN>"
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]}, ...]
```

**Projeto 3 — `task-manager-api`** (`python app.py` + smoke test):

```
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000

$ curl -s http://127.0.0.1:5000/health
{"status": "ok", "timestamp": "2026-08-03 00:53:35.962024+00:00"}

$ curl -s http://127.0.0.1:5000/tasks
[{"id": 1, "title": "Implementar autenticação JWT", "status": "pending", "overdue": true, ...}, ...]

$ curl -s -X DELETE http://127.0.0.1:5000/tasks/1
{"error": "Token de autenticação ausente"}
```

O último log confirma que a proteção adicionada na Fase 3 (findings HIGH de endpoints destrutivos sem
autenticação) está de fato ativa: a exclusão só é aceita com um JWT válido.

### Observações sobre o comportamento da skill em stacks diferentes

- **Nenhum arquivo de `reference/*.md` precisou ser editado** entre os 3 projetos — apenas copiado
  (`.agents/skills/refactor-arch/` inteiro) do `code-smells-project` para os outros dois, confirmando
  o critério de agnosticismo de tecnologia definido no planejamento.
- A Fase 1 identificou corretamente a diferença de **paradigma de persistência**: SQL cru via
  `sqlite3` nos projetos 1 e 2, versus ORM (`Flask-SQLAlchemy`) no projeto 3 — o que mudou o tipo de
  finding de N+1 encontrado (cursor manual em loop vs. `Model.query.get()` em loop), sem precisar de
  regras separadas por ORM/driver.
- No **projeto 2 (Node/Express)**, a skill reconheceu a classe `AppManager` como um God Object mesmo
  sendo uma classe (não um módulo de funções soltas como no projeto 1) — o sinal de detecção genérico
  ("um único arquivo/módulo concentra rotas + regra de negócio + acesso a dados para múltiplos
  domínios") se aplicou independente do paradigma (funcional vs. orientado a objetos).
- No **projeto 3**, a skill não tratou "já ter pastas separadas" como sinônimo de "arquitetura
  correta" — ela reportou HIGH para lógica de negócio nas rotas mesmo com `models/`/`routes/`/
  `services/` já existindo, e a Fase 3 evoluiu a estrutura existente (moveu validação para dentro de
  `services/`) em vez de recriar a árvore do zero, confirmando a regra de "migração incremental".
- A diferença de **maturidade de segurança inicial** entre os projetos também apareceu nos totais: o
  projeto 3 (parcialmente organizado) teve *menos* HIGH (2) que o projeto 1 (5), mas ainda assim 3
  CRITICAL — mostrando que a skill não "relaxa" a auditoria de segurança só porque a arquitetura
  parece mais madura.

---

## D) Como Executar

### Pré-requisitos

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)** instalado e autenticado
  (`claude` disponível no PATH). É a ferramenta usada nesta entrega. O mesmo conceito de skill se aplica a outros agentes que suportam por padrão o `.agents/`.
- **Python 3.12+** com `venv`/`uv` (projetos 1 e 3 — Flask).
- **Node.js 18+** com `npm` (projeto 2 — Express).
- `git` e `curl` (para clonar o repositório e fazer smoke tests dos endpoints).

### Comandos para executar a skill em cada projeto

A skill já está commitada em cada projeto (`.agents/skills/refactor-arch/`, com o symlink
`.claude/skills/refactor-arch`), então não é necessário recriá-la — apenas invocar:

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução:

1. A **Fase 1** imprime o bloco `PHASE 1: PROJECT ANALYSIS` com a stack detectada.
2. A **Fase 2** imprime o `ARCHITECTURE AUDIT REPORT` completo e pausa com
   `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` — responda `y` para prosseguir.
3. A **Fase 3** reestrutura o projeto e imprime `PHASE 3: REFACTORING COMPLETE` com a nova árvore de
   diretórios e o checklist de validação (boot + endpoints + zero anti-patterns).

Para reproduzir a skill em um projeto novo (fora deste repositório), basta copiar a pasta inteira
`.agents/skills/refactor-arch/` (ou `.claude/skills/refactor-arch/`, se preferir sem symlink) para
dentro do projeto-alvo, sem editar nenhum arquivo — esse é o próprio teste de agnosticismo descrito
na seção B.

### Como validar que a refatoração funcionou

Depois da Fase 3, valide manualmente que a aplicação de fato sobe e responde (a própria skill já faz
isso antes de reportar sucesso, mas é possível reconferir):

```bash
# Projeto 1 — code-smells-project
cd code-smells-project
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # ajuste os valores conforme necessário
.venv/bin/python app.py &
curl -s http://127.0.0.1:5000/health
curl -s http://127.0.0.1:5000/produtos

# Projeto 2 — ecommerce-api-legacy
cd ecommerce-api-legacy
npm install
cp .env.example .env
node src/app.js &
curl -s -X POST http://127.0.0.1:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"joao","eml":"joao@test.com","pwd":"123456","c_id":1,"card":"4111111111111111"}'

# Projeto 3 — task-manager-api
cd task-manager-api
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python seed.py
.venv/bin/python app.py &
curl -s http://127.0.0.1:5000/health
curl -s http://127.0.0.1:5000/tasks
curl -s -X DELETE http://127.0.0.1:5000/tasks/1   # deve retornar 401 sem token
```

Critérios objetivos de sucesso (batidos nos 3 projetos — ver checklists da seção C):

- A aplicação inicia sem exceptions.
- Os endpoints originais continuam respondendo com o mesmo contrato (exceto mudanças de segurança
  documentadas, como exigir `Authorization` em rotas destrutivas).
- Nenhum segredo hardcoded permanece no código-fonte (`grep -R "SECRET\|PASSWORD\|API_KEY"` não deve
  encontrar literais fora de `.env.example`).
- Os relatórios de auditoria em [`reports/`](/reports) refletem os findings eliminados.

---

## Estrutura do repositório

```
.
├── README.md                                     # este documento
├── docs/
│   └── refactor-arch-skill-requirements.md       # documento de planejamento da skill (pré-implementação)
├── reports/
│   ├── audit-project-1.md                        # saída da Fase 2 — code-smells-project
│   ├── audit-project-2.md                        # saída da Fase 2 — ecommerce-api-legacy
│   └── audit-project-3.md                        # saída da Fase 2 — task-manager-api
├── code-smells-project/                          # Projeto 1 (Python/Flask) — já refatorado
│   └── .agents/skills/refactor-arch/              # skill original (+ symlink em .claude/skills/)
├── ecommerce-api-legacy/                         # Projeto 2 (Node.js/Express) — já refatorado
│   └── .agents/skills/refactor-arch/              # cópia da skill (+ symlink em .claude/skills/)
└── task-manager-api/                             # Projeto 3 (Python/Flask) — já refatorado
    └── .agents/skills/refactor-arch/              # cópia da skill (+ symlink em .claude/skills/)
```

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills
