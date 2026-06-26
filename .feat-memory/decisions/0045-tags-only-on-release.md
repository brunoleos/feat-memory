---
id: ADR-0045
date: 2026-06-26
status: accepted
version: 1.8.0
supersedes: null
superseded_by: null
affects_features: [F-0035]
related: [ADR-0020, ADR-0042]
tags: [release, versioning, git, tags, methodology]
---

# ADR-0045 · Tags só no `release`; bump de VERSION continua per-commit

## Contexto

O gate ADR-0020 bumpa VERSION a cada commit de código — útil para ver a versão evoluindo. Mas casar cada bump com uma git tag poluía o histórico: muitas tags para estados de desenvolvimento que nunca foram releases de verdade (o projeto sequer está publicado).

## Decisão

Mantém-se o **bump de VERSION per-commit** (ADR-0020 intacto — a versão evolui visivelmente). A **criação de git tag deixa de ser per-commit**: só o comando `feat-memory release` cria tag, e ela leva o nome da **versão atual** (`v<VERSION>`). O `release` **não bumpa** (os commits já bumparam): congela o `UNRELEASED.md` em `changelog/<VERSION>.md`, commita o congelamento e cria a tag `v<VERSION>`. A versão vira um contador vivo; a tag marca um release real.

## Alternativas rejeitadas

- **Tag por commit (status quo da sessão):** polui o git com tags que não marcam release.
- **Parar de bumpar per-commit (mover o bump para o release):** perde a evolução visível da versão, que o mantenedor quer manter.
- **`release` bumpa a versão:** redundante — os commits já bumparam; o release só fotografa a versão corrente.
