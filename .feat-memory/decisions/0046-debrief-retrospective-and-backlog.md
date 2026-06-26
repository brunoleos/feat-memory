---
id: ADR-0046
date: 2026-06-26
status: accepted
version: 2.1.0
supersedes: null
superseded_by: null
affects_features: [F-0038, F-0039]
related: [ADR-0004, ADR-0041, ADR-0043]
tags: [debrief, retrospective, suggestions, methodology]
---

# ADR-0046 · Retrospectiva inline na debrief + backlog de sugestões commitado

## Contexto

O "checkpoint" original pretendia ser uma retrospectiva por-agente, mas degenerou (ADR-0043). A reflexão genuína — o que funcionou, bugs, achados, e **propostas de evolução do próprio sistema de agentes** — não tinha lar. Lição empírica (e da skill `session-retrospective` da iPEN): a narrativa por-sessão **não** deve persistir (apodrece como o checkpoint); só pendências acionáveis ficam.

## Decisão

A `memory-debrief` (mesmo momento — fechar sessão; **não** uma 5ª skill, ADR-0004) **absorve a retrospectiva**: ao fechar, reflete **inline** (escopo, bugs, achados, resumo honesto) e roteia as saídas duráveis para os lares certos (release→`UNRELEASED`, decisão→ADR, capacidade→Feature). Propostas de evolução do sistema (skill/regra/ADR/refactor) entram, com **ask-before-register**, num backlog **commitado**: `.feat-memory/suggestions.md`. Diferente da iPEN (gitignored), o backlog é **versionado** — é a tese de memória durável do feat-memory; serve de funil pré-feature e de **fallback de retomada** quando o `UNRELEASED` está vazio (a bootstrap oferece candidatos).

## Alternativas rejeitadas

- **Persistir a narrativa por-sessão** (o checkpoint de novo): apodrece.
- **5ª skill de retrospectiva:** duplica o gatilho da debrief — é o mesmo momento (ADR-0004).
- **Backlog gitignored (como na iPEN):** contradiz a memória durável e multiagente do feat-memory.
