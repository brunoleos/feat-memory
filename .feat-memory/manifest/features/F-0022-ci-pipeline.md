---
id: F-0022
name: ci-pipeline
status: shipped
introduced: 2026-06-03
version: 0.11.0
user_value: >
  cada push/PR roda pytest + audit estrito numa matriz Linux/macOS/Windows,
  tornando a portabilidade C1 verificável por execução (não só declarada) e
  servindo de segunda linha de defesa para commits que pularam o pre-commit.
contracts:
  api:
    - .github/workflows/ci.yml
  tests: []
acceptance:
  - {id: A1, pattern: event, trigger: "push em main ou abertura de PR", response: "ci.yml roda a matriz {ubuntu,macos,windows} × {3.11,3.12}: install editable, pytest, `feat-memory audit --strict --json`"}
  - {id: A2, pattern: state, state: "pytest falha ou audit emite issue/error em qualquer célula da matriz", response: "o job falha (fail-fast desligado para ver todas as plataformas)"}
  - {id: A3, pattern: ubiquitous, requirement: "workflow não usa shell script (C1) — só comandos diretos no YAML"}
depends_on: [F-0020]
decisions: [ADR-0026]
---

# F-0022 · ci-pipeline

Sem teste — o artefato é o próprio workflow declarativo. A matriz cross-OS é o
ponto: C1 deixa de ser promessa e vira execução. O `audit --strict` no CI fecha o
furo deixado pelo `--no-verify` do pre-commit (ADR-0008). F-0020 = release-status
crosscheck, que o audit do CI exercita.
