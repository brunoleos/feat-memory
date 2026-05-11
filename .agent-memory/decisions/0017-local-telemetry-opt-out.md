---
id: ADR-0017
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0014]
related: [ADR-0008, ADR-0013, ADR-0014, ADR-0016]
tags: [telemetry, observability, privacy, dogfooding]
---

# ADR-0017 · Telemetria local opt-out de aderência ao protocolo

## Contexto

A metodologia vive ou morre da disciplina de invocar `/memory-bootstrap` no início e `/memory-debrief` antes do commit. Não havia feedback sobre se isso de fato acontecia. Risco simétrico: investir num mecanismo que ninguém usa ou (pior) que vaze dados além do projeto local. ADR-0013 já reservou `telemetry_enabled` em `.meta.yaml` antecipando esta decisão — opt-out é o caminho (opt-in vira peso morto sem ativação; privacidade contra si mesmo não faz sentido).

## Decisão

Módulo `telemetry.py` com `record(event, **fields)`. Lê `.meta.yaml::telemetry_enabled`; se `false`, retorna sem escrever. Caso contrário anexa linha JSON em `.agent-memory/.telemetry.jsonl` com `ts`, `version`, `event`, `**fields`. Erros silenciosos — telemetria nunca quebra fluxo do usuário. Subcomando `agent-memory log` lista (com `--since DAYS`, `--event NAME`, `--json`, `--summary` que agrega contagem + taxa de adesão). Eventos canônicos: `session_start` (com `state_read: bool`) emitido por bootstrap, `debrief_run` (com `features_touched`) emitido por debrief. Skills invocam via shell (`agent-memory record`) — qualquer agente que rode shell grava. **`.telemetry.jsonl` no `.gitignore` template** — telemetria é dado pessoal do dev, não memória do projeto; versionar distribuiria padrões de uso individual entre colaboradores.

## Alternativas rejeitadas

- **Opt-in**: peso morto sem ativação; privacidade contra si mesmo não tem custo real.
- **Versionar no Git**: distribuiria uso individual, gera conflitos de merge constantes.
- **Schema validado (Pydantic/JSON Schema)**: overhead; eventos extensíveis e consumo tolerante a campos opcionais.
- **Backend remoto** (mesmo opcional): muda a natureza do contrato com o usuário; local-only mantém previsibilidade total.
- **YAML em vez de JSONL**: JSON parsável por `jq` direto e `json.loads` sem dep extra.
