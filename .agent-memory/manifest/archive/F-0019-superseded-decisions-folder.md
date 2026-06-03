---
id: F-0019
name: superseded-decisions-folder
status: shipped
introduced: 2026-05-11
version: 0.9.0
user_value: >
  ADRs com `status: superseded` vivem em `decisions/superseded/` com INDEX
  próprio (espelho de `manifest/archive/` para features). Desonera o INDEX
  principal de decisões carregado por memory-bootstrap mantendo IDs
  citáveis e resolvíveis.
contracts:
  api:
    - src/agent_memory/shared/paths.py::SUPERSEDED_DIR
    - src/agent_memory/memory/indexing.py::gen_superseded_decisions_index
    - src/agent_memory/memory/indexing.py::regenerate_all_indexes
    - src/agent_memory/governance/audit.py::_resolve_active_decision_paths
    - src/agent_memory/governance/audit.py::run_audit
    - src/agent_memory/memory/propose_adr.py::next_adr_number
  tests:
    - tests/test_superseded_decisions.py
acceptance:
  - {id: A1, pattern: ubiquitous, requirement: "audit varre `decisions/` e `decisions/superseded/` para validação de schema; ambos populam a lista de decisions passada ao crosscheck"}
  - {id: A2, pattern: state, state: "active_decisions de STATE.md lista ADR-NNNN que vive em `decisions/superseded/`", response: "crosscheck encontra; nenhum Issue emitido (espelho de F-0011 para archive de features)"}
  - {id: A3, pattern: event, trigger: "`agent-memory audit` executa com superseded populado", response: "regenera `decisions/INDEX.md` (sem superseded) e `decisions/superseded/INDEX.md` (só superseded); ambos com mesmas colunas"}
  - {id: A4, pattern: ubiquitous, requirement: "`propose_adr.next_adr_number` agrega IDs de DECISIONS_DIR + SUPERSEDED_DIR + PROPOSALS_DIR — colisão de número impossível"}
  - {id: A5, pattern: ubiquitous, requirement: "movimentação de ADR para superseded é manual via `git mv` — não há subcomando dedicado (ADR-0015 continua válida para `agent-memory archive`)"}
depends_on: [F-0011]
decisions: [ADR-0023]
---
