---
id: F-0017
name: memory-governance-split
status: shipped
introduced: 2026-05-05
version: 0.7.0
user_value: Separa o pacote em três subpacotes (shared, memory, governance) com regra de dependência hierárquica `shared ⇐ memory ⇐ governance`. Permite ao consumidor operar puramente em memória sem invocar governança. UX do CLI inalterada.
contracts:
  api:
    - src/feat_memory/shared/paths.py
    - src/feat_memory/shared/parsing.py
    - src/feat_memory/memory/schemas.py
    - src/feat_memory/memory/indexing.py
    - src/feat_memory/governance/audit.py
    - src/feat_memory/cli.py
    - src/feat_memory/deploy.py
  tests:
    - tests/
acceptance:
  - {id: A1, pattern: ubiquitous, requirement: "nenhum módulo de memory.* importa de governance.* — verificável via grep"}
  - {id: A2, pattern: ubiquitous, requirement: "shared.* importa apenas stdlib + deps externas (pyyaml)"}
  - {id: A3, pattern: event, trigger: "`feat-memory deploy <target> --no-hooks`", response: "target recebe artefatos de memória completos sem hook de governança"}
  - {id: A4, pattern: ubiquitous, requirement: "todos os subcomandos pré-existentes mantêm interface idêntica (Liskov-safe na superfície externa)"}
  - {id: A5, pattern: state, state: "`feat-memory --help` invocado", response: "subcomandos agrupados em Memória / Governança via grupos argparse"}
  - {id: A6, pattern: ubiquitous, requirement: "pre-commit hook continua invocando subcomandos via shell — refactor não toca o contrato com Git"}
depends_on: [F-0001, F-0002]
decisions: [ADR-0021]
---

# F-0017 · memory-governance-split

`audit` fica em Memória no `--help` (entrada validacional) mesmo vivendo em `governance/` por orquestrar métricas/drift/freshness. ADR-0021 explica a escolha por um pacote / um CLI / três subpacotes (vs dois pacotes pip ou dois CLIs).
