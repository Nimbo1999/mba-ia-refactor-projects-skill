# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para o padrão MVC pela skill
`refactor-arch`.

## Como rodar

```bash
npm install
cp .env.example .env   # ajuste os valores conforme necessário
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds
automaticamente no boot.

Exemplos de requisições estão em `api.http`. Os endpoints administrativos
(`GET /api/admin/financial-report` e `DELETE /api/users/:id`) exigem o header
`Authorization: Bearer <ADMIN_TOKEN>`, com o valor definido em `.env`.

## Estrutura do projeto

```
src/
├── config/       # variáveis de ambiente (.env) e logger estruturado
├── db/           # conexão sqlite + schema/seed
├── models/       # acesso a dados por entidade (users, courses, enrollments, payments, audit_logs)
├── services/     # regras de negócio (checkout, relatório financeiro, exclusão de usuário, senha, cache)
├── controllers/  # orquestração HTTP, sem SQL nem lógica de negócio
├── middlewares/  # autenticação de admin e tratamento de erro centralizado
├── routes/       # mapeamento de rota → controller
└── app.js        # composition root
```
