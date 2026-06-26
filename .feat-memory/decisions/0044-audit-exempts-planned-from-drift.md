---
id: ADR-0044
date: 2026-06-26
status: accepted
version: 1.6.0
supersedes: null
superseded_by: null
affects_features: []
related: [ADR-0041, ADR-0024]
tags: [audit, manifest, drift, planned, methodology]
---

# ADR-0044 · Audit isenta features `planned` do drift de contracts

## Contexto

A doutrina ADR-0041 manda escrever Features `planned` cedo — antes do código. Mas `validate_feature` tratava "caminho de `contracts` inexistente" como drift para qualquer status, e o pre-commit hook roda `audit --strict` (drift → erro). Resultado: ancorar uma feature `planned`, cujo `api`/`tests` ainda não existem, **bloqueava o commit** — a doutrina era inviável na prática. Descoberto via dogfooding ao ancorar F-0035..0037.

## Decisão

O check de existência de path de `contracts` passa a **pular features com `status: planned`**. Para uma feature `planned`, o `contracts` é um **alvo pretendido**, não um caminho que sumiu — drift só faz sentido para o que afirma estar construído (`in_progress`/`shipped`). Assim a doutrina de ancorar cedo (ADR-0041) convive com o gate `--strict`.

## Alternativas rejeitadas

- **Manter o check para `planned`:** inviabiliza ADR-0041 — não dá para ancorar antes do código.
- **`contracts` vazio em features `planned`:** o campo é obrigatório e o alvo é sinal útil para a retomada; esvaziar perde informação.
- **Hook deixar de usar `--strict`:** enfraquece o gate para todos os casos por causa de um; o alvo cirúrgico é só o status `planned`.
