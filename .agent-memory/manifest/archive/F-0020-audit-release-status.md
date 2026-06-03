---
id: F-0020
name: audit-release-status
status: shipped
introduced: 2026-06-03
version: 0.10.0
user_value: >
  audit detecta feature `in_progress` cujo `version` já foi released
  (CHANGELOG/tag) — a "memória mentirosa" no formato que F-0011 não pegava — e
  destaca STATE velho no relatório. Fecha o gap que deixou 11 features fantasma
  e 23 dias de staleness passarem clean.
contracts:
  api:
    - src/agent_memory/governance/audit.py::released_versions
    - src/agent_memory/governance/audit.py::validate_release_status
    - src/agent_memory/governance/audit.py::run_audit
    - src/agent_memory/governance/audit.py::print_report
    - src/agent_memory/governance/audit.py::STALENESS_WARN_HOURS
  tests:
    - tests/test_release_status.py
acceptance:
  - {id: A1, pattern: state, state: "feature tem status=in_progress e version consta em released_versions (CHANGELOG ## [X.Y.Z] ou tag vX.Y.Z)", response: "Issue severity=warning citando o ID e a version; promovida a error sob --strict"}
  - {id: A2, pattern: ubiquitous, requirement: "feature shipped, ou com version ausente, ou com version não-released nunca gera o warning"}
  - {id: A3, pattern: unwanted, trigger: "audit roda sem CHANGELOG e sem tags Git", response: "released_versions retorna set vazio; validate_release_status não emite nada (fail-soft)"}
  - {id: A4, pattern: event, trigger: "print_report formata frescor de STATE acima de STALENESS_WARN_HOURS (14 dias)", response: "linha de frescor recebe aviso visual; NÃO vira Issue (não afeta exit code nem --strict)"}
  - {id: A5, pattern: ubiquitous, requirement: "staleness no commit continua sendo F-0013 (soft, fail-open); F-0020 não a promove a Issue — ADR-0024"}
depends_on: [F-0011]
decisions: [ADR-0024]
---

# F-0020 · audit-release-status

Codifica a lição do drift que esta feature corrigiu: o cross-check de status↔release
é Issue (bloqueia sob `--strict` — mentira factual), o frescor velho é só destaque
visual (nudge — higiene). A assimetria é deliberada e está em ADR-0024. `released_versions`
reúne CHANGELOG + tags como fonte dupla, fail-soft.
