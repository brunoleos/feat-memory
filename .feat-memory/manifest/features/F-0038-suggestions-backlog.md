---
id: F-0038
name: suggestions-backlog
status: shipped
introduced: 2026-06-26
version: 2.1.0
user_value: Propostas de evolução do sistema (skills/regras/ADRs/refactors) vivem num backlog commitado em .feat-memory/suggestions.md — funil pré-feature e fallback de retomada quando nada está em voo.
contracts:
  api: src/feat_memory/deploy.py::deploy_suggestions
  tests: tests/test_deploy.py
acceptance:
  - {id: A1, pattern: event, trigger: "feat-memory deploy é invocado", response: "cria .feat-memory/suggestions.md se ausente (pula se existe)"}
  - {id: A2, pattern: ubiquitous, requirement: "o backlog é commitado/versionado, não gitignored (memória durável)"}
  - {id: A3, pattern: state, state: "changelog/UNRELEASED.md vazio", response: "a bootstrap oferece candidatos do backlog como próximo foco"}
depends_on: [F-0036]
decisions: [ADR-0046]
---
