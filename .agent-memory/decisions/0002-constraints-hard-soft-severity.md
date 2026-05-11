---
id: ADR-0002
date: 2026-04-28
version: v0.1.0
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0002]
related: []
tags: [schema, audit, constraints]
---

# ADR-0002 · Constraints com severity hard/soft

## Contexto

Restrições não são uniformes em peso — algumas são invariantes (PII em logs, validação de borda), outras são convenções (docstrings, ordem de imports). Tratar todas igualmente produz dois problemas simétricos: tudo-hard bloqueia trabalho legítimo e treina bypass; tudo-soft afoga regras críticas no ruído.

## Decisão

Cada entrada em `AGENTS.md::constraints` declara `severity: hard | soft` no frontmatter. `hard` bloqueia via `agent-memory audit --strict` (pre-commit + CI); `soft` gera warning sem alterar exit code. Mudança entre níveis exige ADR — garante que calibração de regras críticas permaneça deliberada. Risco: inflar a lista classificando tudo como hard "por garantia", recriando o problema; mitigado pela exigência de ADR e pela contagem de violações por severity no relatório.

## Alternativas rejeitadas

- **Apenas hard**: força omitir convenções valiosas, constituição empobrecida.
- **Apenas soft**: enfraquece regras que realmente não podem ser violadas (PII, compliance).
- **Três níveis (info/warn/error)**: ganho marginal não compensa o custo de calibração; dois níveis cobrem 95% dos casos.
