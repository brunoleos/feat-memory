---
id: F-0014
name: local-telemetry
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: >
  Dá ao mantenedor visibilidade local sobre adesão ao ritual da
  metodologia (`/memory-bootstrap` no início, `/memory-debrief`
  antes do commit) sem rede, sem serviço, sem custo de privacidade.
  Eventos JSONL append-only em `.agent-memory/.telemetry.jsonl`
  (gitignored — dado pessoal de adoção, não memória do projeto).
  Default ligado, kill switch em `.meta.yaml::telemetry_enabled=false`.
contracts:
  api:
    - src/agent_memory/governance/telemetry.py::record
    - src/agent_memory/governance/telemetry.py::run_log
    - src/agent_memory/governance/telemetry.py::run_record
  tests:
    - tests/test_telemetry.py
acceptance:
  - id: A1
    pattern: event
    trigger: "`agent-memory record session_start state_read=true` é invocado"
    response: >
      anexa uma linha JSON em `.agent-memory/.telemetry.jsonl` com
      `ts`, `version` (de .meta.yaml), `event=session_start` e
      campos extras (`state_read=true`); sai com 0
  - id: A2
    pattern: state
    state: ".agent-memory/.meta.yaml contém `telemetry_enabled: false`"
    response: >
      `record` retorna sem escrever; nenhum arquivo é criado nem
      modificado, exit 0
  - id: A3
    pattern: event
    trigger: "`agent-memory log` é invocado"
    response: >
      lista os eventos do JSONL (mais recente primeiro), formato tabular
      curto com `ts`, `event`, e campos extras; sai com 0
  - id: A4
    pattern: optional
    feature: "a flag --since DAYS for fornecida"
    response: >
      `log` filtra eventos cujo `ts` está dentro da janela de N dias
      a partir do agora (UTC)
  - id: A5
    pattern: optional
    feature: "a flag --summary for fornecida"
    response: >
      `log` agrega: total por evento + taxa de adesão derivada
      (`session_start` com `state_read=true` / total `session_start`)
  - id: A6
    pattern: ubiquitous
    requirement: >
      `record` é silencioso em qualquer erro de I/O ou parsing (telemetria
      nunca pode quebrar um fluxo do usuário); chamadores podem assumir
      que `record` retorna sem exceção
  - id: A7
    pattern: ubiquitous
    requirement: >
      `.agent-memory/.telemetry.jsonl` está no `.gitignore` template do
      deploy — telemetria é local-only por construção; versionar
      distribuiria padrões de uso individual entre colaboradores
depends_on: [F-0010]
decisions: [ADR-0013, ADR-0017]
---

# F-0014 · local-telemetry

## Comportamento

Telemetria local opt-out via novo módulo [src/agent_memory/governance/telemetry.py](src/agent_memory/governance/telemetry.py).

**Gravação.** `agent-memory record <event> [field=value ...]` invoca `telemetry.record(event, **fields)` que lê `.meta.yaml`, respeita `telemetry_enabled: false`, e anexa linha JSON em `.agent-memory/.telemetry.jsonl` com `ts`, `version`, `event` e campos extras. Erros silenciosos.

**Leitura.** `agent-memory log [--since 7d] [--event NAME] [--json] [--summary]` lê o JSONL, filtra por janela ou evento, agrega taxa de adesão se `--summary`.

**Skills atualizadas.** [skills/memory-bootstrap/SKILL.md](skills/memory-bootstrap/SKILL.md) emite `session_start` com `state_read=true|false`. [skills/memory-debrief/SKILL.md](skills/memory-debrief/SKILL.md) emite `debrief_run` com features tocadas. Acoplamento via shell call (`agent-memory record`), não dependência Python — qualquer agente capaz de invocar shell consegue gravar.

**`.gitignore`.** [src/agent_memory/memory/data/templates/.gitignore](src/agent_memory/memory/data/templates/.gitignore) (novo) declara `.agent-memory/.telemetry.jsonl` ignorado. Atualmente o deploy só garante `.agent-memory-deploy/`; F-0014 estende com a regra de telemetria local. Telemetria é dado pessoal do dev, não memória do projeto.
