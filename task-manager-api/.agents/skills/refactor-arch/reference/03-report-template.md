# Template do Relatório de Auditoria (Fase 2)

> Use este formato **exatamente** — inclusive marcadores, ordem das seções e nomes dos campos —
> para garantir saída determinística entre execuções e projetos. Preencha os campos entre `<>`
> com os valores reais detectados; remova os `<>` no output final.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto analisado>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<M> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Título curto do anti-pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: <o que foi encontrado, em 1-2 frases objetivas>
Impact: <consequência prática — segurança, manutenibilidade, performance>
Recommendation: <ação concreta de correção, referenciando o playbook quando aplicável>

### [<SEVERIDADE>] <Título curto do anti-pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: <...>
Impact: <...>
Recommendation: <...>

<... repetir um bloco "### [<SEVERIDADE>]" por finding, ordenados CRITICAL → HIGH → MEDIUM → LOW ...>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

- **Project**: nome do diretório raiz do projeto analisado (não o nome da skill).
- **Stack**: linguagem + framework detectados na Fase 1.
- **Files/lines**: use a contagem real de arquivos-fonte da Fase 1; a contagem de linhas pode ser
  aproximada (`~N`), mas deve refletir a ordem de grandeza real do código analisado.
- **Summary**: a soma dos 4 números deve ser igual ao `Total` no rodapé e ao número de blocos
  `### [<SEVERIDADE>]` no relatório.
- **Título do finding**: use o nome do anti-pattern do catálogo (ex.: "SQL Injection",
  "Hardcoded Credentials", "God Class / God Method"), sem reformular livremente.
- **File**: sempre caminho relativo ao projeto + linha(s) exatas (`arquivo.py:12` ou
  `arquivo.py:47-53`). Nunca omita a linha nem aproxime.
- **Ordenação**: todos os findings `CRITICAL` primeiro, depois `HIGH`, depois `MEDIUM`, depois
  `LOW`. Dentro da mesma severidade, mantenha a ordem em que os anti-patterns aparecem no
  catálogo de referência.
- **Pergunta final**: deve ser feita literalmente como `Phase 2 complete. Proceed with
  refactoring (Phase 3)? [y/n]` e a execução deve parar ali, aguardando resposta do usuário antes
  de qualquer ação da Fase 3.
- Este mesmo bloco de texto (do `====` inicial até a pergunta final) é o conteúdo que deve ser
  salvo, sem edições, em `reports/audit-<projeto>.md` quando solicitado.
