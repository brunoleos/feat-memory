---
id: F-0018
name: consumer-version-notice
status: in_progress
introduced: 2026-05-05
version: 0.7.0
user_value: Notifica (soft) quando a versão do CLI instalada via pipx difere de `.meta.yaml::version`. Fecha o loop que F-0010 e F-0016 abriram — "consumidor desatualizado" vira sinal observável em vez de surpresa quando uma skill faz algo inesperado.
contracts:
  api:
    - src/agent_memory/governance/version_check.py::consumer_version_notice
    - src/agent_memory/governance/version_check.py::run
    - src/agent_memory/governance/audit.py::run
  tests:
    - tests/test_version_check.py
acceptance:
  - {id: A1, pattern: state, state: "`.meta.yaml::version` ≠ `__version__`", response: "`consumer_version_notice` retorna texto com ambas as versões + sugestão de re-deploy; audit imprime na stderr após relatório, sem alterar exit"}
  - {id: A2, pattern: state, state: "versões iguais", response: "`consumer_version_notice` retorna None; audit não emite linha extra"}
  - {id: A3, pattern: unwanted, trigger: "`.meta.yaml` ausente (consumidor pré-v0.6)", response: "retorna None — fail-soft"}
  - {id: A4, pattern: state, state: "`.meta.yaml::version_check_enabled=false`", response: "retorna None (coerente com telemetry_enabled de F-0014)"}
  - {id: A5, pattern: event, trigger: "`agent-memory version-check` invocado", response: "imprime notice ou \"atualizado: vX.Y.Z\"; exit 0 — subcomando standalone para CI"}
  - {id: A6, pattern: ubiquitous, requirement: "exit do `agent-memory audit` NUNCA é alterado — soft sempre, ADR-0008 preservado"}
depends_on: [F-0010, F-0017]
decisions: [ADR-0022]
---
