---
id: ADR-0006
date: 2026-04-29
version: v0.2.0
status: superseded
supersedes: ADR-0005
superseded_by: ADR-0007
affects_features: [F-0001]
related: []
tags: [installation, distribution]
---

# ADR-0006 · Gitignore `.agent-memory/` e re-clone em fresh checkouts (v0.2.0)

## Contexto

ADR-0005 versionava `.agent-memory/` no consumidor. Cada `git pull` da tool produzia diff gigante no histórico do projeto, poluindo `git log` com mudanças que não são do projeto. Duplicação dificultava upgrade coordenado entre projetos.

## Decisão

`.agent-memory/` continua sendo clonado dentro do projeto, mas vira **gitignored**. `deploy.py` adiciona automaticamente a entrada ao `.gitignore` via bloco com sentinelas (idempotente). Update vira `rm -rf .agent-memory && git clone --branch <tag> ... .agent-memory && python .agent-memory/deploy.py`. Skills passam a ser sempre atualizadas pelo deploy (em vez de puladas) — são conteúdo de metodologia, refletem sempre a versão corrente.

**Substituída por ADR-0007** porque fresh checkouts não eram mais autocontidos (re-clone manual antes do deploy) e o fluxo `rm -rf` era frágil, propenso a deixar versões inconsistentes entre projetos.

## Alternativas rejeitadas

- **Manter v0.1.0 versionado**: já documentado o custo de poluição do histórico.
- **Pip install**: novamente considerado e adiado — tool ainda sem entry point CLI nem layout adequado; mudança grande demais para um único incremento.
