---
id: F-0024
name: constraint-enforcement
status: shipped
introduced: 2026-06-03
version: 0.12.0
user_value: >
  Constraints da constituição deixam de ser só prosa declarativa: cada uma pode
  declarar um bloco `check` que o `agent-memory audit` executa contra o
  repositório. A violação herda a severity da constraint (hard bloqueia o build,
  soft gera warning). Torna a "camada de constitution" enforced — o diferencial
  do projeto no ecossistema spec-driven development.
contracts:
  api:
    - src/agent_memory/governance/constraints.py::check_constraints
    - src/agent_memory/governance/constraints.py::validate_check_shape
    - src/agent_memory/governance/constraints.py::CHECKERS
    - src/agent_memory/governance/audit.py::run_audit
    - src/agent_memory/governance/audit.py::print_report
  tests:
    - tests/test_constraints.py
acceptance:
  - {id: A1, pattern: optional, feature: "uma constraint declara um bloco `check` bem-formado", response: "audit executa o checker do conjunto fechado e emite um Issue por violação"}
  - {id: A2, pattern: state, state: "uma violação é detectada", response: "o Issue herda a severity da constraint — hard→error (bloqueia sempre), soft→warning"}
  - {id: A3, pattern: unwanted, trigger: "o bloco `check` é malformado (type desconhecido, param faltando, regex inválido, ou dependencies sem allow/forbid)", response: "Issue severity=error de schema, bloqueando o build como EARS malformado"}
  - {id: A4, pattern: ubiquitous, requirement: "constraint sem bloco `check` permanece puramente declarativa e nunca gera Issue (back-compat)"}
  - {id: A5, pattern: event, trigger: "o checker `dependencies` encontra um pacote no manifesto fora da allowlist (ou dentro da forbid)", response: "violação citando o nome do pacote; normaliza nomes PEP 503-ish e cobre pyproject.toml/requirements.txt/package.json"}
  - {id: A6, pattern: ubiquitous, requirement: "o conjunto de checkers é fechado — forbid_paths, require_paths, forbid_pattern, require_pattern, dependencies — composto via YAML sem escrever Python (ADR-0028)"}
depends_on: [F-0002]
decisions: [ADR-0028]
---

# F-0024 · constraint-enforcement

Promove o item "Linting de constraints hard" de `[Adiado]` a flagship sob o
posicionamento "ser a melhor camada de constitution do SDD" (ADR-0028). A razão
que adiava o item — "cada regra exige um validador próprio" — é resolvida por um
**conjunto fechado** de checkers genéricos compostos via YAML, não um validador por
regra. Vive em `governance/constraints.py` (não em `memory/schemas.py`) porque
executar checker varre a árvore — governança, não schema (ADR-0021). Dogfood:
C1 (`forbid_paths`) e C2 (`dependencies`) deste repo passam a ser checadas a cada
audit. C3/C4 ficam declarativas — limitação honesta.
