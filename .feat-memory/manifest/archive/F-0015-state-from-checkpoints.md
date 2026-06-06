---
id: F-0015
name: state-from-checkpoints
status: shipped
introduced: 2026-05-04
version: 0.6.0
user_value: Inverte STATE.md de fonte da verdade para view derivada de checkpoints append-only, eliminando reescrita destrutiva por debriefs apressados. memory-bootstrap continua lendo o mesmo arquivo (Liskov-safe).
contracts:
  api:
    - src/feat_memory/memory/checkpoints.py::run_checkpoint
    - src/feat_memory/memory/checkpoints.py::run_state_rebuild
    - src/feat_memory/memory/checkpoints.py::render_state
    - src/feat_memory/memory/checkpoints.py::append_checkpoint
    - src/feat_memory/memory/migrate.py::run
  tests:
    - tests/test_checkpoints.py
acceptance:
  - {id: A1, pattern: event, trigger: "`feat-memory checkpoint --summary '...' [--current ...] [--next ...]` invocado", response: "cria `.feat-memory/checkpoints/YYYY-MM-DD-HHMMSS.md` (schema em ADR-0019) e regera STATE.md"}
  - {id: A2, pattern: ubiquitous, requirement: "checkpoints existentes nunca são modificados; colisão de timestamp sufixa com `-N`"}
  - {id: A3, pattern: state, state: "há ao menos um checkpoint", response: "STATE.md gerado com Current/Next do mais recente, Recent dos N anteriores (default 5)"}
  - {id: A4, pattern: event, trigger: "`feat-memory state-rebuild` invocado", response: "regera STATE.md sem criar novo checkpoint (recovery)"}
  - {id: A5, pattern: event, trigger: "`feat-memory migrate --to=checkpoints` em checkpoints/ vazio", response: "lê STATE.md legado, cria checkpoint inicial com author=migration, preserva Recent legado no body"}
  - {id: A6, pattern: state, state: "checkpoints/ já tem arquivos", response: "migrate é idempotente — mensagem informativa, exit 0"}
  - {id: A7, pattern: optional, feature: "`.meta.yaml::state_view_window` definido", response: "renderer usa N=window (default N=1)"}
  - {id: A8, pattern: ubiquitous, requirement: "memory-debrief invoca `feat-memory checkpoint` em vez de reescrever STATE.md — reescritas destrutivas impossíveis por construção"}
depends_on: [F-0008, F-0014]
decisions: [ADR-0018, ADR-0019]
---
