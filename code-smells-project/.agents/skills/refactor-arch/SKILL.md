---
name: refactor-arch
description: 'Analisa, audita e refatora uma codebase de backend legada para o padrão MVC (Model-View-Controller), de forma agnóstica de linguagem e framework. Use quando o usuário pedir para analisar a stack/arquitetura de um projeto, auditar code smells e anti-patterns de segurança/qualidade, gerar um relatório de auditoria arquitetural, ou refatorar/reestruturar um backend legado para MVC. Funciona com qualquer stack de backend (Python/Flask, Node/Express, Django, Java/Spring, etc.) sem exigir configuração ou ajuste prévio.'
argument-hint: '[caminho-do-projeto] (opcional; padrão: diretório de trabalho atual)'
---

# refactor-arch

## Visão geral

Esta skill audita e refatora **qualquer** codebase de backend, em 3 fases sequenciais e
obrigatórias:

1. **Fase 1 — Análise**: detecta linguagem, framework, dependências, banco de dados, domínio da
   aplicação e arquitetura atual. **Não modifica nenhum arquivo.**
2. **Fase 2 — Auditoria**: cruza o código-fonte contra o catálogo de anti-patterns, gera um
   relatório estruturado por severidade e **pausa, pedindo confirmação humana explícita**
   (`[y/n]`) antes de prosseguir. **Não modifica nenhum arquivo.**
3. **Fase 3 — Refatoração**: só executa depois de confirmação explícita do usuário na Fase 2;
   reestrutura o projeto para o padrão MVC, elimina os anti-patterns encontrados e **valida** que
   a aplicação continua subindo e respondendo nos mesmos endpoints.

As fases são estritamente sequenciais: nunca pule a confirmação da Fase 2 para ir direto à
Fase 3, mesmo que o usuário peça "refatore tudo" — sempre gere e apresente o relatório de
auditoria primeiro.

## Princípio central: agnosticismo de tecnologia

Esta skill nunca deve assumir uma linguagem, framework, nome de arquivo, nome de tabela ou
domínio de negócio específico. Todo o raciocínio das 3 fases é guiado por **sinais estruturais
genéricos** (ex.: "arquivo de manifest de dependências", "string concatenada formando SQL",
"pasta chamada `models`/`controllers`/`routes`"), nunca por literais como `app.py` ou `produtos`.
Os arquivos de referência trazem exemplos em múltiplas linguagens (no mínimo Python e
JavaScript) apenas como ilustração de cada heurística — nunca como a única forma reconhecida.
Trate o "projeto alvo" sempre como o diretório de trabalho atual (ou o caminho passado em
`argument-hint`), nunca um nome de projeto fixo.

## Regras gerais (valem para as 3 fases)

- Ignore a pasta da própria skill (`.agents/`, `.claude/`), artefatos de VCS/dependências
  (`.git`, `node_modules`, `venv`, `.venv`, `__pycache__`, `dist`, `build`, `*.egg-info`) e
  arquivos de dados/binários (`*.db`, `*.sqlite`, `*.log`) ao escanear o código-fonte.
- Todas as saídas impressas ao usuário devem seguir **exatamente** os formatos definidos nos
  arquivos de referência (blocos `PHASE 1`, `ARCHITECTURE AUDIT REPORT`, `PHASE 3`), para manter
  saída determinística entre execuções e projetos.
- Nunca invente números: contagens de arquivos, tabelas, findings e linhas devem refletir o que
  foi de fato observado no código.
- Se o projeto já tiver alguma separação de camadas (ex.: `models/`, `routes/` já existem), a
  Fase 1 deve descrever isso com precisão e a Fase 3 deve **evoluir** essa estrutura em vez de
  presumir que tudo precisa ser criado do zero.

## Fase 1 — Análise

**Objetivo:** entender a stack e a arquitetura atual sem alterar nada.

**Procedimento:**
1. Liste os arquivos-fonte do projeto (excluindo o que está listado em "Regras gerais").
2. Aplique as heurísticas de [`reference/01-project-analysis.md`](./reference/01-project-analysis.md)
   para detectar: linguagem, framework (+ versão, se houver manifest), dependências relevantes,
   banco de dados/ORM, domínio da aplicação e uma frase descrevendo a arquitetura atual.
3. Conte arquivos-fonte analisados e tabelas/coleções de banco detectadas.
4. Imprima o resumo exatamente no formato abaixo (substituindo os valores pelos detectados):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework> <versão, se disponível>
Dependencies:  <lista curta de dependências relevantes>
Domain:        <domínio inferido>
Architecture:  <frase descrevendo a arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas/coleções, se houver>
================================
```

5. Não crie, edite nem apague nenhum arquivo nesta fase.

## Fase 2 — Auditoria

**Objetivo:** produzir um relatório de auditoria confiável e pausar para confirmação.

**Procedimento:**
1. Aplique cada anti-pattern de [`reference/02-anti-patterns-catalog.md`](./reference/02-anti-patterns-catalog.md)
   sobre todo o código-fonte identificado na Fase 1, incluindo a subseção de **APIs/padrões
   deprecated** quando aplicável à stack detectada.
2. Para cada problema encontrado, monte um finding com: severidade, título, arquivo, linha(s)
   exatas, descrição, impacto e recomendação, seguindo
   [`reference/03-report-template.md`](./reference/03-report-template.md) à risca.
3. Garanta um mínimo de 5 findings, incluindo pelo menos 1 `CRITICAL` ou `HIGH`. Se a varredura
   inicial encontrar menos que isso, revise o código com mais atenção antes de concluir a fase —
   não invente findings artificiais.
4. Ordene os findings por severidade: `CRITICAL` → `HIGH` → `MEDIUM` → `LOW`.
5. Gere a contagem-resumo (`CRITICAL: n | HIGH: n | MEDIUM: n | LOW: n`) e imprima o relatório
   completo no formato do template de referência.
6. **Pare e pergunte explicitamente ao usuário**: `Phase 2 complete. Proceed with refactoring
   (Phase 3)? [y/n]`.
   - Se a resposta for negativa (ou ambígua), **encerre a execução sem tocar em nenhum arquivo**
     e informe que a Fase 3 não foi executada.
   - Se a resposta for afirmativa, prossiga para a Fase 3.
7. Guarde o relatório completo gerado nesta fase — ele deve poder ser salvo depois em
   `reports/audit-*.md` sem precisar ser regerado.
8. Não modifique nenhum arquivo nesta fase, independente da resposta do usuário.

## Fase 3 — Refatoração

**Objetivo:** eliminar os anti-patterns e reestruturar o projeto para MVC, validando o resultado.

**Procedimento:**
1. Use [`reference/04-architecture-guidelines.md`](./reference/04-architecture-guidelines.md)
   para definir a árvore de diretórios alvo (`config/`, `models/`, `views`/`routes/`,
   `controllers/`, middleware de erro centralizado, entry point/composition root), adaptando-a à
   convenção idiomática da linguagem/framework detectados na Fase 1.
2. Para cada finding do relatório da Fase 2, aplique a transformação correspondente de
   [`reference/05-refactoring-playbook.md`](./reference/05-refactoring-playbook.md) — elimine o
   problema de verdade (não apenas comente ou documente), por exemplo: mover credenciais para
   variáveis de ambiente/config, parametrizar queries SQL, extrair lógica de negócio dos
   controllers/rotas para uma camada de serviço/model, remover/proteger endpoints administrativos
   perigosos, eliminar duplicação, substituir `print`/`console.log` por logging estruturado, etc.
3. Preserve o comportamento externo: os mesmos paths e contratos de request/response devem
   continuar funcionando, salvo correções de segurança que precisam mudar o comportamento (nesse
   caso, documente a mudança explicitamente no resumo final).
4. Valide o resultado:
   - Inicie a aplicação (comando idiomático da stack, ex.: `python app.py`,
     `flask run`, `npm start`) e confirme que sobe sem exceptions.
   - Faça smoke tests dos endpoints originais (ex.: `curl` em rotas de leitura/health) e confirme
     que respondem com o status/formato esperado.
   - Se algo quebrar, corrija antes de declarar a fase concluída — nunca reporte sucesso com
     validação falhando.
5. Imprima o resumo final exatamente no formato abaixo:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios nova, gerada dinamicamente>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

Se algum item de validação falhar, substitua `✓` por `✗` e descreva o problema — nunca marque
como sucesso algo que não foi de fato verificado.

## Arquivos de referência

| Arquivo | Fase(s) | Conteúdo |
|---|---|---|
| [`reference/01-project-analysis.md`](./reference/01-project-analysis.md) | 1 | Heurísticas de detecção de stack, banco de dados, domínio e arquitetura |
| [`reference/02-anti-patterns-catalog.md`](./reference/02-anti-patterns-catalog.md) | 2 | Catálogo de anti-patterns com sinais de detecção e severidade |
| [`reference/03-report-template.md`](./reference/03-report-template.md) | 2 | Template exato do relatório de auditoria |
| [`reference/04-architecture-guidelines.md`](./reference/04-architecture-guidelines.md) | 3 | Definição do padrão MVC alvo e responsabilidades de camada |
| [`reference/05-refactoring-playbook.md`](./reference/05-refactoring-playbook.md) | 3 | Transformações antes/depois mapeadas ao catálogo de anti-patterns |
