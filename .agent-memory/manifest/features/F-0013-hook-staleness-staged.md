---
id: F-0013
name: hook-staleness-staged
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: Pre-commit avisa (soft, exit 0) quando o commit toca código sem incluir STATE.md no staging — captura `/memory-debrief` esquecido no momento mais barato de intervir.
contracts:
  api:
    - src/agent_memory/governance/check_staleness.py::run
    - src/agent_memory/governance/check_staleness.py::staged_warning
    - src/agent_memory/governance/data/hooks/pre-commit
  tests:
    - tests/test_check_staleness.py
acceptance:
  - {id: A1, pattern: event, trigger: "`check-staleness-staged` invocado com paths de código no staging mas sem STATE.md", response: "stderr amarela sugerindo /memory-debrief; exit 0"}
  - {id: A2, pattern: state, state: "staging inclui STATE.md", response: "exit 0 silencioso, mesmo com código no staging"}
  - {id: A3, pattern: state, state: "staging só com paths não-código (.agent-memory/, tests/, docs/, README.md)", response: "exit 0 silencioso"}
  - {id: A4, pattern: ubiquitous, requirement: "exit é sempre 0 — soft sempre; sinal vive na stderr"}
  - {id: A5, pattern: event, trigger: "pre-commit hook executa", response: "invoca check-staleness-staged independentemente do returncode do audit"}
  - {id: A6, pattern: unwanted, trigger: "`git diff --cached` falha", response: "retorna sem aviso (fail-soft)"}
depends_on: [F-0005, F-0011]
decisions: [ADR-0016]
---

# F-0013 · hook-staleness-staged

Reusa `_is_code_path` de audit.py — uma única definição de "código" para history-side (F-0011), staged-side (F-0013) e version-bump-side (F-0016).
