---
id: F-0036
name: unreleased-living-state
status: planned
introduced: 2026-06-26
version: 2.0.0
user_value: O foco em-voo e o orçamento de retomada vivem em changelog/UNRELEASED.md; o conjunto ativo de F/ADR é derivado das referências das entradas, sem lista hand-maintained.
contracts:
  api: src/feat_memory/memory/changelog.py::derive_active_refs
  tests: tests/test_unreleased.py
acceptance:
  - {id: A1, pattern: event, trigger: "memory-bootstrap carrega o contexto inicial", response: "lê changelog/UNRELEASED.md e expande apenas as F/ADR referenciadas nas entradas"}
  - {id: A2, pattern: state, state: "UNRELEASED.md está vazio", response: "a retomada aponta para o último release no INDEX (ou o backlog, na Fase 2)"}
  - {id: A3, pattern: ubiquitous, requirement: "não existe STATE.md nem lista active_* hand-maintained"}
depends_on: [F-0035]
decisions: [ADR-0043]
---
