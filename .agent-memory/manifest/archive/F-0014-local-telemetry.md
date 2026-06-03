---
id: F-0014
name: local-telemetry
status: shipped
introduced: 2026-05-04
version: 0.6.0
user_value: Telemetria local em `.agent-memory/.telemetry.jsonl` (gitignored) dá ao mantenedor visibilidade sobre adesão ao ritual (bootstrap, debrief). Sem rede, sem serviço, sem custo de privacidade. Default ligado, kill switch via `.meta.yaml::telemetry_enabled=false`.
contracts:
  api:
    - src/agent_memory/governance/telemetry.py::record
    - src/agent_memory/governance/telemetry.py::run_log
    - src/agent_memory/governance/telemetry.py::run_record
  tests:
    - tests/test_telemetry.py
acceptance:
  - {id: A1, pattern: event, trigger: "`agent-memory record <event> [k=v...]` invocado", response: "anexa linha JSON ao JSONL com ts, version, event e campos extras; exit 0"}
  - {id: A2, pattern: state, state: "`.meta.yaml::telemetry_enabled=false`", response: "`record` retorna sem escrever; exit 0"}
  - {id: A3, pattern: event, trigger: "`agent-memory log` invocado", response: "lista eventos (mais recente primeiro) em tabular curto"}
  - {id: A4, pattern: optional, feature: "flag `--since DAYS`", response: "filtra eventos dentro da janela em UTC"}
  - {id: A5, pattern: optional, feature: "flag `--summary`", response: "agrega total por evento + taxa de adesão (session_start com state_read=true / total)"}
  - {id: A6, pattern: ubiquitous, requirement: "`record` é silencioso em qualquer erro de I/O — telemetria nunca quebra fluxo do usuário"}
  - {id: A7, pattern: ubiquitous, requirement: "JSONL está em .gitignore template — telemetria é dado pessoal do dev, não memória de projeto"}
depends_on: [F-0010]
decisions: [ADR-0013, ADR-0017]
---
