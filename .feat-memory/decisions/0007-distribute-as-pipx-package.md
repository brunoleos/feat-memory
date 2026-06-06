---
id: ADR-0007
date: 2026-04-29
version: v0.3.0
status: accepted
supersedes: ADR-0006
superseded_by: null
affects_features: [F-0001]
related: []
tags: [installation, distribution, packaging, breaking-change]
---

# ADR-0007 · Distribuir via pipx; CLI no PATH; src layout (v0.3.0, BREAKING)

## Contexto

ADR-0006 eliminou poluição de histórico Git mas três custos residuais ficaram: cada projeto exigia clone separado da tool, o fluxo de update (`rm -rf` + clone + deploy) era frágil e deixava versões inconsistentes, e executar a tool exigia path explícito (`python .feat-memory/deploy.py`).

## Decisão

**BREAKING CHANGE.** Distribuir como pacote Python via `pipx`. Layout move para `src/feat_memory/` (src layout padrão). Templates, skills e hook ficam em `data/` acessados via `importlib.resources` (funciona em editable install e em wheel). `pyproject.toml` define entry point `feat-memory = "feat_memory.cli:main"` com subcomandos (`deploy`, `audit`, `propose-adr`, `migrate`); versão lida de `VERSION` na raiz. Instalação recomendada: `git clone <tool> ~/dev/feat-memory && pipx install -e ~/dev/feat-memory` — editable install faz `git pull` no clone refletir em todos os consumidores sem tocar em cada projeto. Estado transiente de deploy move de `.feat-memory/.merge-queue` para `<projeto>/.feat-memory-deploy/` (gitignored). Pacote ainda não está na PyPI (planejado).

## Alternativas rejeitadas

- **Manter v0.2.0**: custos já documentados.
- **Publicar direto na PyPI**: queremos validar a interface CLI em uso real antes de versionamento estável publicado.
- **Scripts standalone + wrapper shell**: viola constraint pure-Python; não resolve instalação one-shot.
