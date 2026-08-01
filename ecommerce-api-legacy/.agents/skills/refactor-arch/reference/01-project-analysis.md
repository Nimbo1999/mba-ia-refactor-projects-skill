# Análise de Projeto — Heurísticas de Detecção (Fase 1)

> Estas heurísticas são agnósticas de linguagem. Cada regra é descrita primeiro em termos
> estruturais genéricos, com exemplos de Python e JavaScript como ilustração — nunca como a única
> forma reconhecida. Sempre que possível, prefira ler arquivos de manifest/configuração a
> adivinhar pela extensão de arquivo isolada.

## 1. Detecção de linguagem e framework

**Sinal genérico:** presença de um arquivo de manifest de dependências na raiz (ou próximo dela)
do projeto, mais a extensão predominante dos arquivos-fonte.

| Manifest encontrado | Linguagem provável | Como extrair framework/versão |
|---|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml` | Python | Procurar linhas como `flask==3.1.1`, `django>=4`, `fastapi`; a versão vem depois de `==`/`>=`/`~=` |
| `package.json` | JavaScript/TypeScript (Node.js) | Ler `dependencies`/`devDependencies`; `express`, `fastify`, `koa`, `nestjs` indicam o framework; version string acompanha a chave |
| `pom.xml`, `build.gradle` | Java/Kotlin | Procurar `spring-boot`, `quarkus`, `micronaut` nas dependências declaradas |
| `Gemfile` | Ruby | Procurar `rails`, `sinatra` |
| `go.mod` | Go | Procurar `gin-gonic/gin`, `labstack/echo`, `gorilla/mux` |
| `*.csproj` | C#/.NET | Procurar `Microsoft.AspNetCore.*` |

Se nenhum manifest for encontrado, use a extensão predominante dos arquivos-fonte (`.py`, `.js`,
`.ts`, `.rb`, `.go`, `.java`, ...) como fallback para a linguagem, e procure por padrões de
importação típicos de framework no código (ver tabela abaixo) para inferir o framework mesmo sem
manifest.

**Sinais de framework web no próprio código-fonte** (independem do manifest):

- Python: `from flask import Flask` / `Flask(__name__)` → Flask. `from django...` /
  `INSTALLED_APPS` → Django. `from fastapi import FastAPI` → FastAPI.
- JavaScript: `require('express')` / `import express from 'express'` → Express. `require('fastify')`
  → Fastify. `@nestjs/core` → NestJS.
- Em qualquer linguagem: procure o construtor/objeto de aplicação (`app = Framework()`,
  `const app = framework()`) e as chamadas de registro de rota (`app.route`, `app.get`,
  `app.add_url_rule`, `@app.get(...)`, `router.get(...)`) para confirmar qual framework está de
  fato orquestrando as requisições HTTP.

## 2. Dependências relevantes

Liste, do manifest de dependências, apenas os pacotes que impactam arquitetura/segurança/qualidade
(framework web, driver/ORM de banco, CORS, autenticação, validação, testes). Ignore dependências
transitivas ou de baixo nível quando o manifest as listar separadamente.

## 3. Detecção de banco de dados e camada de persistência

**Sinal genérico:** import de biblioteca de conexão/driver de banco, ou presença de comandos de
definição de schema (`CREATE TABLE`, migrações, definição de coleção/schema de ODM).

| Sinal no código | Banco/tecnologia provável |
|---|---|
| `import sqlite3`, `sqlite3.connect(...)`, arquivo `*.db`/`*.sqlite` | SQLite |
| `psycopg2`, `import pg`, `DATABASE_URL` com `postgres://` | PostgreSQL |
| `pymysql`, `mysql.connector`, `mysql2` (Node) | MySQL/MariaDB |
| `pymongo`, `mongoose`, `MongoClient` | MongoDB |
| `sqlalchemy`, `django.db.models.Model`, `sequelize`, `prisma`, `typeorm` | ORM presente |
| Strings SQL cruas (`SELECT`, `INSERT INTO`, `UPDATE ... SET`, `DELETE FROM`) concatenadas ou
  interpoladas diretamente no código de acesso a dados | SQL cru, sem ORM |

**ORM vs. SQL cru:** se as operações de dado são feitas via métodos de um objeto/classe mapeado
(ex.: `Produto.objects.filter(...)`, `Model.query.filter_by(...)`, `Produto.findAll()`), é ORM.
Se são strings de SQL montadas manualmente (com `+`, f-string, template literals ou `%`), é SQL
cru — e deve ser avaliado também pelo catálogo de anti-patterns (risco de SQL Injection).

**Tabelas/coleções:** extraia os nomes literais que aparecem em `CREATE TABLE <nome>`,
`class <Nome>(Model)` / `class <Nome>(db.Model)`, `mongoose.model('<Nome>', ...)`, ou migrações
equivalentes.

## 4. Inferência de domínio da aplicação

**Sinal genérico:** nomes de rotas HTTP, nomes de tabelas/entidades e nomes de funções/métodos de
negócio, agrupados por radical semântico comum (ex.: `produto`/`product`, `pedido`/`order`,
`usuario`/`user`, `tarefa`/`task`, `curso`/`course`).

Procedimento:
1. Colete todos os paths de rota registrados (`app.route`, `app.add_url_rule`, `router.get`,
   decorators de rota) e os nomes de tabela/entidade detectados na seção 3.
2. Agrupe por substantivo/radical comum, ignorando prefixos técnicos (`/api`, `/v1`).
3. Descreva o domínio em uma frase curta citando as 2–4 entidades mais centrais (ex.: "E-commerce
   API — produtos, pedidos, usuários", "Task Manager — tarefas, categorias, usuários").
4. Se o domínio não for óbvio a partir dos nomes (ex.: nomes genéricos como `Item`, `Resource`),
   descreva-o em termos do que as rotas efetivamente fazem (ex.: "API de gerenciamento de recursos
   genéricos com CRUD e autenticação").

## 5. Descrição da arquitetura atual

Avalie os seguintes sinais estruturais, independente da linguagem:

- **Número de camadas físicas**: quantos arquivos/módulos distintos concentram roteamento, lógica
  de negócio e acesso a dados? Se um único arquivo (ou dois ou três arquivos monolíticos) contém
  praticamente tudo, é "monolítica, sem separação de camadas". Se já existem pastas/módulos
  dedicados a `models`, `controllers`/`services`, `routes`/`views`, descreva como "parcialmente
  organizada" ou "em camadas", conforme o nível de separação observado.
- **Presença de camadas nomeadas**: procure diretórios/módulos com nomes convencionais
  (`models/`, `controllers/`, `routes/`, `views/`, `services/`, `repositories/`, `middlewares/`).
  A presença desses nomes não implica que a separação está correta — apenas que existe intenção
  de camada, o que a Fase 2 deve verificar em detalhe.
- **Entry point**: identifique o arquivo que instancia a aplicação e a inicia (`if __name__ ==
  "__main__": app.run(...)`, `app.listen(...)`, `manage.py runserver`). Isso ajuda a entender se
  existe um composition root único ou se a inicialização está espalhada.
- **Frase-resumo**: combine os sinais acima em uma única frase objetiva, no mesmo estilo de
  "Monolítica — tudo em N arquivos, sem separação de camadas" ou "Parcialmente organizada — models
  e routes separados, mas lógica de negócio ainda misturada nos controllers".

## 6. Contagem de arquivos-fonte

Conte apenas arquivos-fonte da linguagem principal detectada (ex.: `.py`, `.js`/`.ts`), excluindo:
testes automatizados (a menos que o projeto seja majoritariamente testes), arquivos de
configuração declarativa (`*.json`, `*.toml`, `*.cfg`, `*.ini`), migrações geradas automaticamente
e qualquer diretório listado nas "Regras gerais" do `SKILL.md` (dependências, VCS, pasta da própria
skill).
