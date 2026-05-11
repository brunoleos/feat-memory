---
id: ADR-0022
date: 2026-05-05
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0018]
related: [ADR-0008, ADR-0013, ADR-0020, ADR-0021]
tags: [governance, observability, consumer-notice, soft-warning]
---

# ADR-0022 · Notificação soft ao consumidor quando CLI difere de `.meta.yaml::version`

## Contexto

ADR-0013 grava `.meta.yaml::version` no consumidor; ADR-0020 garante que `__version__` evolua honestamente. Faltava o elo: o consumidor não sabe quando sua estrutura foi produzida por CLI antigo. Skills evoluem, novos templates/sentinelas chegam via re-deploy; sem notificação o usuário descobre tarde, quando uma skill faz algo inesperado. Usuário declarou explicitamente: "as skills aqui evoluem, então tenho que saber quando os projetos consumidores precisam se atualizar".

## Decisão

Módulo `governance/version_check.py` com `consumer_version_notice(root) -> str | None`: lê `.meta.yaml::version`, compara com `agent_memory.__version__`, retorna texto se diferentes em qualquer direção; `None` se iguais, `.meta.yaml` ausente, ou `version_check_enabled: false`. **Integração:** `audit.run` invoca após `print_report()` e imprime na stderr (amarelo com `isatty`); **não muda exit code**. Subcomando standalone `agent-memory version-check` para invocação direta (CI, scripts). Disable via `.meta.yaml::version_check_enabled: false` (default `true`, coerente com `telemetry_enabled`). **Primeira versão não distingue patch/minor/major** — simplicidade primeiro; se houver fricção real (N notices/dia por patch sem efeito), evolução natural é suprimir patch-only. **Não fazemos auto-redeploy** — toca arquivos do consumidor, decisão do humano.

## Alternativas rejeitadas

- **Hard (bloqueia)**: atualizar não é obrigatório (consumer pode pinar versão antiga deliberadamente); hard é ferramenta errada para "informar".
- **Notice em todos os subcomandos**: ruído de fundo; audit é o lugar natural (usuário já olhando o estado).
- **Distinguir semver no primeiro corte**: complexidade prematura; evolui se houver fricção.
- **`minimum_required_version` no sentinel block**: overhead de manutenção (cada release atualiza sentinels) sem ganho claro vs notice por diff.
- **Notice apenas quando consumer < CLI**: regra simétrica captura o caso raro (CLI rodando contra consumer mais novo, sintoma de pipx desatualizado).
- **Auto-redeploy**: toca templates/hooks/skills; deve ser decisão explícita, especialmente em times com vários agentes.
