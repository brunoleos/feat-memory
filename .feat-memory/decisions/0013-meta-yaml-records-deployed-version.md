---
id: ADR-0013
date: 2026-05-03
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0010, F-0011, F-0014]
related: [ADR-0007, ADR-0011]
tags: [deploy, meta, version, observability]
---

# ADR-0013 · Deploy grava `.feat-memory/.meta.yaml` com versão e timestamp

## Contexto

A versão do `feat-memory` que produziu a estrutura de um consumidor só vivia implícita nas URLs `blob/v{VERSION}/...` interpoladas no template — descobrir exigia parsing frágil de markdown e nenhum subcomando reportava "auditado contra v0.6.0". Três usos imediatos pediam versão como dado de primeira classe: audit cross-check (F-0011), telemetria (F-0014), e suporte ao usuário ("qual versão você está rodando?").

## Decisão

`feat-memory deploy` grava `.feat-memory/.meta.yaml` no consumidor com `schema_version`, `version`, `deployed_at` (ISO 8601 UTC), `cli_path` (abspath do executável), `telemetry_enabled: true` (kill switch para F-0014, default ligado por ADR-0017). CLI ganha flag `--version` no parser raiz. Helper `read_meta(root)` retorna dict ou `None` se ausente — tolerância deliberada para consumidores pré-v0.6 degradarem graciosamente. `.meta.yaml` **é versionado no Git** — metadata de instalação paralela a `package.json`/`pyproject.toml`. `cli_path` gera churn entre máquinas; aceito pelo valor diagnóstico em projetos solo, pacificável via `.gitattributes` em times. Schema do `.meta.yaml` independente do schema dos artefatos da metodologia.

## Alternativas rejeitadas

- **Embutir versão em frontmatter de AGENTS.md**: mistura metadata de instalação com config editável; polui separação de responsabilidades.
- **Usar `pyproject.toml` da CLI via `importlib.metadata`**: inviável — consumidor não tem dependência declarada; CLI vive no ambiente Python, não no projeto.
- **Arquivo ignorado pelo Git** (`.cache/version`): reduziria churn de `cli_path` mas perderia rastreabilidade histórica.
- **JSON em vez de YAML**: resto do projeto usa YAML; consistência vence.
