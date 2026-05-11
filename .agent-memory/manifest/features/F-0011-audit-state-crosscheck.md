---
id: F-0011
name: audit-state-crosscheck
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: Captura "memória mentirosa" — STATE.md aponta para F-NNNN ou ADR-NNNN que não existem no disco — antes que o agente confie nessa referência na próxima retomada.
contracts:
  api:
    - src/agent_memory/governance/audit.py::validate_state_crosscheck
    - src/agent_memory/governance/audit.py::validate_state_freshness
    - src/agent_memory/governance/audit.py::run_audit
  tests:
    - tests/test_audit_anti_lying.py
acceptance:
  - {id: A1, pattern: state, state: "active_features lista F-NNNN sem arquivo em manifest/features/ ou manifest/archive/", response: "Issue severity=error; audit retorna exit 1 (bloqueia hook)"}
  - {id: A2, pattern: state, state: "active_decisions lista ADR-NNNN sem arquivo em decisions/", response: "Issue severity=error; exit reflete a falha"}
  - {id: A3, pattern: optional, feature: "flag `--check-staleness[=N]` fornecida", response: "examina commits dos últimos N dias (default 7); se há commit tocando código sem commit tocando STATE.md, emite warning sugerindo /memory-debrief"}
  - {id: A4, pattern: unwanted, trigger: "audit roda fora de repo Git ou sem commits no período", response: "freshness retorna sem warning (fail-soft)"}
  - {id: A5, pattern: ubiquitous, requirement: "crosscheck não duplica drift de contracts — drift verifica contratos contra filesystem; crosscheck verifica IDs de STATE contra arquivos de feature/ADR"}
depends_on: [F-0002]
decisions: [ADR-0014]
---

# F-0011 · audit-state-crosscheck

Crosscheck é hard error e on por default. Staleness é warning soft e opt-in via flag — separação respeita ADR-0008 (fail-open do hook). Heurística de "código" (`_is_code_path`) vive em audit.py e é reusada por F-0013 e F-0016.
