---
id: F-0016
name: check-version-bump
status: shipped
introduced: 2026-05-04
version: 0.6.0
user_value: Pre-commit bloqueia (exit 1) commits que tocam código sem atualizar VERSION, garantindo que `__version__`, `.meta.yaml::version` e telemetria sejam honestos. Auto opt-in — no-op em projetos sem arquivo VERSION.
contracts:
  api:
    - src/feat_memory/governance/check_version_bump.py::needs_bump
    - src/feat_memory/governance/check_version_bump.py::run
    - src/feat_memory/governance/data/hooks/pre-commit
  tests:
    - tests/test_check_version_bump.py
acceptance:
  - {id: A1, pattern: event, trigger: "staging com paths de código sem incluir VERSION", response: "stderr vermelha com instrução SemVer e bypass via `--no-verify`; exit 1 (bloqueia)"}
  - {id: A2, pattern: state, state: "staging inclui VERSION", response: "exit 0 silencioso"}
  - {id: A3, pattern: state, state: "staging só com paths não-código", response: "exit 0 silencioso"}
  - {id: A4, pattern: unwanted, trigger: "VERSION ausente na raiz", response: "exit 0 (auto opt-in — sem VERSION, sem guard)"}
  - {id: A5, pattern: event, trigger: "pre-commit executa", response: "invoca após audit e check-staleness; exit code do hook é `or` dos três"}
  - {id: A6, pattern: ubiquitous, requirement: "heurística de código importada de `audit._is_code_path` — uma definição compartilhada"}
depends_on: [F-0005, F-0011]
decisions: [ADR-0020]
---

# F-0016 · check-version-bump

Primeiro check **hard** no hook (audit já era hard por schema; este é hard por política de release). ADR-0020 explica a exceção a ADR-0008 fail-open: versão mentirosa quebra F-0010/F-0014/F-0018 silenciosamente. Bypass via `--no-verify` cobre WIP.
