# Catálogo de Anti-patterns (Fase 2)

> Cada anti-pattern é descrito primeiro em termos agnósticos de linguagem ("o conceito"), seguido
> de sinais de detecção acionáveis e exemplos ilustrativos em Python e/ou JavaScript. A ausência
> de um exemplo em uma linguagem específica não significa que o anti-pattern não se aplique a ela
> — aplique sempre o conceito genérico ao código real, em qualquer stack.

## Critérios de severidade (referência)

- **CRITICAL**: falhas graves de arquitetura ou segurança que impedem funcionamento correto,
  expõem dados sensíveis, ou violam completamente a separação de responsabilidades.
- **HIGH**: fortes violações do padrão MVC/SOLID que dificultam muito manutenção e testes.
- **MEDIUM**: problemas de padronização, duplicação de código ou gargalos de performance
  moderada.
- **LOW**: melhorias de legibilidade, nomenclatura ruim, "magic numbers".

---

## CRITICAL

### C1 — SQL Injection (concatenação/interpolação de SQL)
**Conceito:** uma query SQL é montada concatenando ou interpolando diretamente valores vindos de
parâmetros de função, request ou input do usuário, em vez de usar placeholders parametrizados.
**Sinais de detecção:**
- Presença de palavras-chave SQL (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `WHERE`) na mesma
  expressão que operadores de concatenação (`+`, `%`, f-string `f"..."`, `.format(...)`, template
  literals `` ` ``) envolvendo uma variável.
- Ausência de placeholders (`?`, `%s`, `$1`, `:nome`) na chamada de execução da query.
- Exemplo (Python): `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`
- Exemplo (JavaScript): `` db.query(`SELECT * FROM users WHERE id = ${id}`) ``

### C2 — Credenciais/segredos hardcoded no código-fonte
**Conceito:** um segredo (chave de API, senha, secret de sessão/JWT, connection string com
credenciais) é atribuído a uma constante literal diretamente no código-fonte versionado, em vez de
vir de variável de ambiente/cofre de segredos.
**Sinais de detecção:**
- Atribuição de string literal a identificadores como `SECRET`, `SECRET_KEY`, `API_KEY`,
  `PASSWORD`, `TOKEN`, `DATABASE_URL` contendo usuário/senha embutidos.
- O mesmo valor sendo reexposto em uma resposta HTTP (endpoint de health-check, debug, etc.).
- Exemplo (Python): `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`
- Exemplo (JavaScript): `const JWT_SECRET = "abc123"`

### C3 — Endpoint administrativo que executa código/SQL arbitrário sem autenticação
**Conceito:** existe uma rota que recebe um comando, script ou query livre do corpo da requisição
e o executa diretamente contra o sistema/banco, sem nenhuma verificação de identidade/autorização.
**Sinais de detecção:**
- Rota que lê um campo do corpo da requisição (`request.json`, `req.body`) e passa esse valor
  diretamente para uma função de execução (`cursor.execute(valor)`, `eval(valor)`, `exec(valor)`,
  `child_process.exec(valor)`) sem middleware/decorator de autenticação antes dela.
- Ausência de qualquer checagem de papel/token na função da rota.

### C4 — Senhas armazenadas/comparadas em texto puro
**Conceito:** senhas de usuário são persistidas e comparadas como texto plano, sem hash
criptográfico unidirecional (bcrypt, scrypt, argon2, PBKDF2).
**Sinais de detecção:**
- Coluna/campo `senha`/`password` recebendo diretamente o valor do request, sem chamada a uma
  função de hashing antes do `INSERT`/`save`.
- Comparação de login feita com `==`/`WHERE senha = ?` comparando o valor puro, em vez de
  `check_password_hash`/`bcrypt.compare`/equivalente.

---

## HIGH

### H1 — God Class / God Module
**Conceito:** um único arquivo/módulo concentra roteamento, regras de negócio, acesso a dados e
formatação de resposta para múltiplos domínios de negócio distintos.
**Sinais de detecção:**
- Um arquivo com centenas de linhas contendo funções para 3+ entidades de negócio diferentes,
  misturando queries de banco, validação e serialização.
- Ausência de qualquer separação em módulos/pastas por responsabilidade.

### H2 — Endpoint destrutivo sem autenticação/autorização
**Conceito:** uma rota que apaga, reseta ou altera em massa dados de produção pode ser chamada por
qualquer cliente, sem exigir identidade autenticada nem papel autorizado.
**Sinais de detecção:**
- Rota HTTP (`DELETE`, `POST`, `PUT`) cujo corpo de implementação executa operações destrutivas
  (`DELETE FROM ...`, `drop`, `truncate`, `reset`) sem decorator/middleware de autenticação
  precedendo o handler.

### H3 — Configuração insegura de produção
**Conceito:** a aplicação roda com flags de desenvolvimento/depuração ativas ou políticas de CORS
totalmente abertas, mesmo quando se declara (ou se comporta) como ambiente de produção.
**Sinais de detecção:**
- `DEBUG = True` / `app.run(debug=True)` / `NODE_ENV` não verificado antes de habilitar
  stack-traces detalhados.
- CORS habilitado sem restrição de origem (`CORS(app)` sem `origins=`, `cors()` sem opções, ou
  header `Access-Control-Allow-Origin: *` fixo).

### H4 — Lógica de negócio dentro de Controllers/Routes
**Conceito:** regras de negócio (cálculos, orquestração multi-etapas, validações complexas,
decisões de fluxo) ficam implementadas diretamente no handler de rota/controller, em vez de uma
camada de serviço/domínio dedicada e testável isoladamente.
**Sinais de detecção:**
- Handler de rota com múltiplos `if`/cálculos de negócio (descontos, totais, regras de estoque)
  antes de simplesmente delegar a uma função de serviço.
- Mesma regra de negócio duplicada em mais de um handler.

### H5 — Estado global mutável / forte acoplamento sem injeção de dependência
**Conceito:** o acesso a um recurso compartilhado (conexão de banco, cache, cliente externo) é
feito por uma variável de módulo mutável referenciada diretamente em toda a aplicação, em vez de
ser injetado/parametrizado.
**Sinais de detecção:**
- Variável de módulo (`global`, `let`/`var` no escopo de módulo) reatribuída dentro de uma função
  "getter" e importada diretamente por múltiplos outros módulos, sem nenhuma abstração
  (factory, container de DI, `app.config`).

---

## MEDIUM

### M1 — Query N+1
**Conceito:** para montar uma lista de itens "pai" com seus relacionados "filho", o código executa
uma query adicional por item dentro de um laço, em vez de uma única query com `JOIN`/`IN`/eager
loading.
**Sinais de detecção:**
- Um `for`/`forEach` que, a cada iteração, abre um novo cursor/chamada de banco
  (`cursor.execute` dentro do loop, `await Model.find(...)` dentro de `.map`/`for`).

### M2 — Duplicação de lógica (serialização, validação, formatação)
**Conceito:** o mesmo mapeamento/transformação de dados (ex.: linha de banco → dicionário/objeto
de resposta) é reescrito de forma idêntica ou quase idêntica em múltiplos pontos do código.
**Sinais de detecção:**
- Blocos de código quase idênticos (mesmas chaves/campos montados manualmente) repetidos em 2+
  funções, sem uma função/serializer compartilhado.

### M3 — Ausência de validação de entrada em rotas
**Conceito:** um endpoint aceita e processa dados de entrada sem validar tipo, presença ou
formato antes de usá-los em lógica de negócio ou persistência.
**Sinais de detecção:**
- Uso direto de `request.json`/`req.body` em uma query ou cálculo sem checagem prévia de
  presença/tipo dos campos esperados.

### M4 — Listas/regras de validação duplicadas e hardcoded
**Conceito:** um conjunto de valores válidos (enum de negócio) é redeclarado como lista/array
literal em mais de um lugar do código, em vez de centralizado em uma única fonte de verdade.
**Sinais de detecção:** o mesmo array/lista de valores literais (categorias, status, papéis)
aparecendo em mais de uma função/arquivo.

---

## LOW

### L1 — Uso de `print`/`console.log` para logging
**Conceito:** mensagens de diagnóstico são emitidas via função de impressão padrão em vez de um
módulo de logging configurável (níveis, formato, destino).
**Sinais de detecção:** chamadas a `print(...)` (Python) ou `console.log/error(...)` (JavaScript)
usadas para registrar eventos de aplicação/erros em código de produção.

### L2 — "Magic numbers"
**Conceito:** valores numéricos de negócio aparecem soltos no meio da lógica, sem nome/constante
que explique seu significado.
**Sinais de detecção:** literais numéricos (além de `0`/`1` triviais) usados em comparações ou
cálculos de negócio sem estarem atribuídos a uma constante nomeada.

### L3 — Nomenclatura pouco descritiva
**Conceito:** identificadores (variáveis, funções, parâmetros) usam nomes genéricos ou
abreviados demais para comunicar sua intenção.
**Sinais de detecção:** nomes como `d`, `x`, `data2`, `tmp`, `foo`, ou nomes de função que não
correspondem ao que o código de fato faz.

---

## Detecção de APIs/padrões deprecated

**Conceito:** o projeto usa uma API, método ou padrão de biblioteca que o próprio
framework/linguagem já marcou como obsoleto (deprecated) ou substituiu por uma alternativa
recomendada, geralmente identificável por avisos de depreciação, changelog do framework, ou
padrões amplamente documentados como legados.
**Sinais de detecção (adapte à stack detectada na Fase 1):**
- Python/Flask: `@app.before_first_request` (removido no Flask 2.3+, use `with app.app_context()`
  na inicialização); uso de `flask.Markup` (mover para `markupsafe.Markup`); `datetime.utcnow()`
  (deprecated em favor de `datetime.now(timezone.utc)` no Python 3.12+).
- Node/Express: middlewares embutidos removidos (`express.bodyParser()` antigo, substituído por
  `express.json()`/`express.urlencoded()`); `new Buffer(...)` (deprecated em favor de
  `Buffer.from(...)`); callbacks de MongoDB driver antigo em vez de Promises/`async-await`.
- Genérico: qualquer chamada que emita warning de depreciação do próprio runtime/framework em
  tempo de execução, ou biblioteca listada como "unmaintained"/"deprecated" no manifest de
  dependências (ex.: anotação no `package.json`/changelog).

Classifique cada API deprecated encontrada como **MEDIUM** por padrão (ou **LOW** se for apenas
cosmético, sem risco de quebra futura), a menos que a API deprecated também configure um problema
de segurança já coberto por outro item do catálogo — nesse caso, use a severidade do item de
segurança correspondente.
