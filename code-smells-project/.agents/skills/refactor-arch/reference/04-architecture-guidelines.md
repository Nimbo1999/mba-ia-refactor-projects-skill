# Guidelines de Arquitetura — Padrão MVC Alvo (Fase 3)

> Estas regras definem a estrutura MVC alvo em termos agnósticos de linguagem. Adapte nomes de
> pastas/arquivos à convenção idiomática da linguagem/framework detectados na Fase 1 (ex.:
> `snake_case.py` em Python, `camelCase.js`/`PascalCase` de classe em JavaScript), mas **as
> responsabilidades de cada camada abaixo não mudam**.

## 1. Responsabilidade de cada camada

### Models (`models/`)
- Únicos responsáveis por acesso a dados e regras de persistência (queries, ORM, validação de
  formato de dado no nível de schema).
- Não conhecem HTTP: não recebem `request`/`response`, não retornam códigos de status.
- Toda query parametrizada — nunca concatenar/interpolar valores externos em SQL.
- Cada model representa uma entidade/domínio coeso (ex.: `produto_model`, `usuario_model`); evite
  um único model cobrindo múltiplas entidades não relacionadas.

### Views / Routes (`views/` ou `routes/`)
- Responsáveis apenas pelo mapeamento HTTP: path, método, parsing de parâmetros de
  rota/querystring, e despachar para o controller correspondente.
- Não contêm lógica de negócio nem acesso direto a dados.
- Agrupe rotas por domínio (ex.: um arquivo de rotas por entidade/recurso), evitando um único
  arquivo de rotas monolítico quando o domínio já justifica separação.

### Controllers (`controllers/`)
- Orquestram o fluxo de uma requisição: validam entrada (ou delegam a um validador/schema),
  chamam models/serviços na ordem correta, tratam erros esperados e formatam a resposta.
- Não contêm SQL nem lógica de negócio pesada (cálculos de domínio, regras multi-etapa) — isso
  deve estar em uma camada de serviço/domínio (pode viver dentro de `models/` ou em um
  `services/` dedicado, conforme a complexidade do projeto) chamada pelo controller.
- Cada controller deve ser testável isoladamente, mockando models/serviços.

### Configuração (`config/`)
- Centraliza leitura de variáveis de ambiente/segredos (`SECRET_KEY`, connection strings, flags de
  ambiente) — nenhum valor sensível deve permanecer hardcoded fora deste módulo, e mesmo aqui o
  valor real deve vir de variável de ambiente (`os.environ`/`process.env`), nunca de um literal.
- Define comportamento por ambiente (dev/test/produção), incluindo desabilitar `debug`/CORS aberto
  fora de desenvolvimento.

### Middleware de erro centralizado
- Um único ponto de tratamento de exceções não capturadas, que padroniza o formato de erro da API
  (ex.: `{"erro": "...", "sucesso": false}` com status HTTP apropriado) e evita vazamento de
  stack-trace/detalhes internos em produção.
- Handlers individuais podem levantar/propagar exceções de domínio específicas; o middleware as
  traduz para respostas HTTP consistentes.

### Entry point / Composition root
- Um único arquivo responsável por instanciar a aplicação, carregar configuração, registrar
  rotas/middlewares e iniciar o servidor.
- Não deve conter lógica de negócio nem definição de rota individual "solta" fora do módulo de
  rotas.

## 2. Regras de nomeação de arquivos/pastas

- Use plural ou singular de forma consistente dentro de cada camada (ex.: sempre
  `models/produto_model.py` ou sempre `models/produto.model.js`), evitando misturar convenções no
  mesmo projeto.
- Nomeie o arquivo pela entidade/domínio que ele representa, nunca por uma abreviação genérica
  (`m1.py`, `stuff.js`).
- Mantenha a mesma convenção de casing já usada no ecossistema da linguagem: `snake_case` para
  módulos Python, `camelCase`/`PascalCase` para arquivos/classes JavaScript, conforme já for
  idiomático na stack detectada.

## 3. Estrutura de diretórios alvo (referência)

```
<raiz-do-projeto>/
├── config/            # variáveis de ambiente, settings por ambiente
├── models/            # acesso a dados, um arquivo por entidade/domínio
├── routes/            # (ou views/) mapeamento HTTP → controller, um arquivo por domínio
├── controllers/        # orquestração do fluxo de request, um arquivo por domínio
├── services/           # (opcional) lógica de negócio complexa extraída dos controllers
├── middlewares/         # tratamento de erro centralizado, autenticação, etc.
└── app.<ext>            # entry point / composition root
```

Adapte nomes de pastas para o idioma/convenção já usada no projeto quando fizer sentido (ex.: um
projeto Django já usa `apps/<app>/models.py`, `views.py`, `urls.py` — nesse caso, **evolua** essa
convenção existente em vez de forçar nomes de pasta diferentes dos idiomáticos do framework).

## 4. Migração incremental para projetos parcialmente organizados

Se a Fase 1 já detectou camadas nomeadas (`models/`, `routes/`, `services/` já existem), a Fase 3
deve:
- Preservar a estrutura de pastas já existente sempre que ela já seguir a responsabilidade correta
  de camada.
- Mover apenas o código que está na camada errada (ex.: SQL cru dentro de um controller) para a
  camada correta, em vez de recriar a árvore inteira do zero.
- Adicionar apenas as pastas/módulos que estiverem genuinamente faltando (ex.: `config/` ausente,
  middleware de erro inexistente).
