---
id: F-0012
name: archive-shipped
status: shipped
introduced: 2026-05-04
version: 0.6.0
user_value: Subcomando `agent-memory archive` move features shipped (e fora de active_features) para `manifest/archive/`, reduzindo o INDEX que memory-bootstrap carrega na retomada. ADRs nunca são arquivados (registro histórico imutável).
contracts:
  api:
    - src/agent_memory/memory/archive.py::run
    - src/agent_memory/memory/archive.py::collect_eligible
    - src/agent_memory/governance/audit.py::run_audit
    - src/agent_memory/governance/audit.py::gen_archive_index
  tests:
    - tests/test_archive.py
acceptance:
  - {id: A1, pattern: event, trigger: "`agent-memory archive` sem flags", response: "lista elegíveis (dry-run); sai 0 sem mover nada"}
  - {id: A2, pattern: event, trigger: "`agent-memory archive --apply`", response: "move via `git mv` (fallback `shutil.move`), regenera ambos os INDEXes, sai 0"}
  - {id: A3, pattern: state, state: "feature shipped E em active_features", response: "não elegível (active vence shipped)"}
  - {id: A4, pattern: ubiquitous, requirement: "`run_audit` valida schema e drift tanto em manifest/features/ quanto em manifest/archive/; INDEXes separados"}
  - {id: A5, pattern: ubiquitous, requirement: "ADRs nunca são arquivados — `superseded_by` cobre semântica de \"não use mais\""}
depends_on: [F-0002, F-0011]
decisions: [ADR-0015]
---

# F-0012 · archive-shipped

Default dry-run inverte convenção habitual deliberadamente: custo de "esqueci o flag" é zero; custo de "movi sem querer" é commit indesejado.
