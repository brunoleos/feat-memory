---
id: F-0011
name: audit-state-crosscheck
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: >
  Captura "memória mentirosa" — quando STATE.md aponta para features
  ou ADRs que não existem no disco — antes que o agente confie nessa
  referência na próxima retomada. Cross-check é hard error e roda por
  default; staleness check (commit recente sem update de STATE) é
  warning soft e opt-in via --check-staleness, respeitando ADR-0008.
contracts:
  api:
    - src/agent_memory/governance/audit.py::validate_state_crosscheck
    - src/agent_memory/governance/audit.py::validate_state_freshness
    - src/agent_memory/governance/audit.py::run_audit
  tests:
    - tests/test_audit_anti_lying.py
acceptance:
  - id: A1
    pattern: state
    state: "active_features de STATE.md lista um F-NNNN sem arquivo correspondente em manifest/features/ ou manifest/archive/"
    response: >
      `validate_state_crosscheck` emite Issue com severity 'error'
      identificando o ID órfão, e `agent-memory audit` retorna exit
      code 1 (bloqueando o pre-commit hook)
  - id: A2
    pattern: state
    state: "active_decisions de STATE.md lista um ADR-NNNN sem arquivo correspondente em decisions/"
    response: >
      `validate_state_crosscheck` emite Issue com severity 'error'
      identificando o ID órfão, e o exit code reflete a falha
  - id: A3
    pattern: ubiquitous
    requirement: >
      `validate_state_crosscheck` busca features em ambos
      `manifest/features/` e `manifest/archive/` (o último previsto
      por F-0012); ID encontrado em qualquer um satisfaz a regra
  - id: A4
    pattern: optional
    feature: "a flag --check-staleness for fornecida"
    response: >
      `validate_state_freshness` examina commits dos últimos 7 dias
      (ou N via --check-staleness=N); se há commits que tocaram
      arquivos de código sem nenhum commit tocando STATE.md, emite
      Issue com severity 'warning' sugerindo `/memory-debrief`
  - id: A5
    pattern: unwanted
    trigger: "audit roda fora de repositório Git ou sem commits no período"
    response: >
      `validate_state_freshness` retorna sem warning (fail-soft);
      a ausência de histórico não deve mascarar como sinal positivo
      nem promover a erro
  - id: A6
    pattern: ubiquitous
    requirement: >
      cross-check NÃO duplica detecção feita por `validate_feature`
      (drift de contracts) — são camadas distintas: drift verifica
      contratos de cada feature contra o filesystem; cross-check
      verifica que cada ID em STATE.md tem um arquivo de feature/ADR
depends_on: [F-0002]
decisions: [ADR-0014]
---

# F-0011 · audit-state-crosscheck

## Comportamento

Adiciona duas validações ao `agent-memory audit`, cobrindo as duas formas mais comuns de "memória mentirosa" em STATE.md:

1. **Cross-check de existência (hard, default-on).** Após carregar features e decisions, [audit.run_audit](src/agent_memory/governance/audit.py) chama `validate_state_crosscheck(state_fm, features, decisions)` que verifica se cada `F-NNNN` em `active_features` tem arquivo em `manifest/features/` ou `manifest/archive/`, e cada `ADR-NNNN` em `active_decisions` tem arquivo em `decisions/`. Falhas viram erros que bloqueiam o pre-commit hook.

2. **Staleness check (soft, opt-in).** Nova `validate_state_freshness(repo_root, days=7)` é invocada apenas com `agent-memory audit --check-staleness[=N]`. Examina `git log` dos últimos N dias; se commits tocaram código (paths fora de `.agent-memory/`, `tests/`, `docs/`, e fora de docs raiz como `README.md`) e nenhum commit tocou `.agent-memory/STATE.md`, emite warning sugerindo `/memory-debrief`.

A política de severities e a heurística de "código" estão em ADR-0014. O cross-check honra a separação ADR-0002 (hard vs soft) e o staleness honra o princípio de fail-open do hook (ADR-0008) por ser opt-in.
