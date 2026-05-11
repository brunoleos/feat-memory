---
id: ADR-0005
date: 2026-04-28
version: v0.1.0
status: superseded
supersedes: null
superseded_by: ADR-0006
affects_features: []
related: []
tags: [installation, distribution]
---

# ADR-0005 · Versionar `.agent-memory/` no consumidor (v0.1.0)

## Contexto

Na v0.1.0 a tool ainda estava sendo validada — sem maturidade para publicação em PyPI ou outro registry. Precisava estratégia de distribuição imediata, sem infraestrutura externa.

## Decisão

Clonar a tool dentro do projeto consumidor em `.agent-memory/` e versionar o diretório. Setup trivial (um `git clone`), projeto autocontido, atualização via `git pull` ou re-clone manual.

**Substituída por ADR-0006** porque a tool inteira (scripts, templates, skills) duplicava em cada projeto consumidor, cada `git pull` produzia diff gigante no histórico, e o `git log` do projeto consumidor ficava poluído com mudanças que pertencem à tool.

## Alternativas rejeitadas

- **Pip install**: exigia publicação na PyPI antes da validação em uso real.
- **Submodule Git**: complexidade operacional (submodule update, init) sem ganho claro nesta fase.
