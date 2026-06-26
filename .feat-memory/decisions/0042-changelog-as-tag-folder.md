---
id: ADR-0042
date: 2026-06-26
status: proposed
version: 2.0.0
supersedes: null
superseded_by: null
affects_features: [F-0035, F-0037]
related: [ADR-0035]
tags: [changelog, history, folder, convention, multiagent]
---

# ADR-0042 · Changelog como pasta por-tag; depreciação de Keep-a-Changelog

## Contexto

O `CHANGELOG.md` monolítico é uma das quatro cópias da história "o que shippou quando" (junto de git tags, checkpoints e a tabela Recent do STATE). Além da duplicação, é um arquivo **quente único** que colide em merge num projeto multiagente — e diverge do padrão interno do próprio feat-memory, onde história durável vive como pasta + `INDEX.md` gerado (`decisions/`, `manifest/`).

## Decisão

O histórico de releases vira a pasta `.feat-memory/changelog/` com **1 arquivo imutável por tag** (`<X.Y.Z>.md`) + `INDEX.md` gerado (mesma máquina de `indexing.py`). **Sem `CHANGELOG.md` na raiz.** Isso **depreca a convenção Keep-a-Changelog** (arquivo único) — decisão explícita do mantenedor: consistência interna (pasta+INDEX) + superfície de merge multiagente pesam mais que a convenção externa. O subcomando `feat-memory release X.Y.Z` orquestra o release (valida bump SemVer, bumpa VERSION, congela `UNRELEASED.md`→`<X.Y.Z>.md`, cria UNRELEASED novo, regenera INDEX, commit + tag `vX.Y.Z`).

## Alternativas rejeitadas

- **Manter o monolito:** quarta cópia da história + arquivo quente que colide em merge — o oposto do que o projeto precisa.
- **Gerar `CHANGELOG.md` raiz a partir da pasta** (honrar Keep-a-Changelog): reintroduz o arquivo quente; o mantenedor deprecou a convenção explicitamente.
