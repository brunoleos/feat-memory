---
id: F-0019
name: audit-resumption-budget-warning
status: in_progress
introduced: 2026-05-05
version: 0.8.1
user_value: >
  Quando os artefatos de bootstrap (AGENT.md + CLAUDE.md + STATE.md +
  INDEXES) excedem `budgets.resumption_max_bytes` definido em AGENT.md,
  `agent-memory audit` agora emite warning explicito apontando para
  `agent-memory archive`. Antes desta feature o cálculo existia mas o
  budget era violado em silêncio — operador ficava com sessões
  sub-otimizadas sem saber que precisava agir.
contracts:
  api:
    - src/agent_memory/governance/audit.py::validate_resumption_budget
    - src/agent_memory/governance/audit.py::_compute_resumption_cost
    - src/agent_memory/governance/audit.py::run_audit
  tests:
    - tests/test_audit_budget.py
acceptance:
  - id: A1
    pattern: state
    state: "custo de retomada (soma de AGENT.md + CLAUDE.md + STATE.md + manifest/INDEX.md + decisions/INDEX.md) excede `budgets.resumption_max_bytes`"
    response: >
      `validate_resumption_budget` emite Issue com severity `warning`
      cuja mensagem cita ambos os valores (cost, max) com separador
      de milhares e sugere remediação via `agent-memory archive` ou
      redução do corpo das features
  - id: A2
    pattern: state
    state: "custo de retomada é igual ao budget (limite exato)"
    response: >
      nenhum Issue é emitido — só estritamente maior dispara warning
  - id: A3
    pattern: ubiquitous
    requirement: >
      severity é sempre `warning` (soft, ADR-0008/ADR-0014); o exit
      code do `agent-memory audit` NÃO é alterado por esta feature
      isoladamente — operador decide quando agir
  - id: A4
    pattern: state
    state: "AGENT.md::budgets::resumption_max_bytes ausente"
    response: >
      `run_audit` cai no default `DEFAULT_RESUMPTION_BUDGET = 12288`
      definido em `memory/schemas.py` — operador pode aumentar o
      budget se a doutrina do projeto exige bootstrap maior
  - id: A5
    pattern: ubiquitous
    requirement: >
      o cálculo de custo é compartilhado entre `compute_metrics`
      (que reporta o número no relatório) e
      `validate_resumption_budget` (que compara com o budget) via
      `_compute_resumption_cost`, garantindo que relatório e
      warning nunca divergem
depends_on: [F-0010, F-0012]
decisions: [ADR-0014]
---

# F-0019 · audit-resumption-budget-warning

## Comportamento

`agent-memory audit` passa a emitir warning soft quando o **custo de retomada** (soma em bytes dos arquivos que `memory-bootstrap` carrega no início de cada sessão) excede o budget configurado em `AGENT.md::budgets::resumption_max_bytes`.

O cálculo de custo já existia em [compute_metrics](src/agent_memory/governance/audit.py) desde a v0.1, mas era apenas informativo no relatório — sem comparação contra o budget. Operadores ficavam meses violando 2× o limite sem qualquer sinal, conforme reportado em [relatório de uso v0.5.0](FUTURE_IMPROVEMENTS.md).

A feature extrai o cálculo para `_compute_resumption_cost()`, reusada por `compute_metrics` (relatório) e `validate_resumption_budget()` (warning). Mensagem do warning aponta para `agent-memory archive` (F-0012, ADR-0015) que é o caminho documentado para reduzir o INDEX de features ativas.

Severity `warning` (não `error`) é coerente com ADR-0014 — o budget é orientação, não regra hard. Operador decide se arquiva, reduz corpo de features ou aumenta o budget no AGENT.md. Roda em todo audit (incluindo via pre-commit hook) — fica visível sem ser interrompedor.
