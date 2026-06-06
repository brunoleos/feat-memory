---
id: F-0005
name: pre-commit-hook
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Bloqueia commits que violam a estrutura dos artefatos de memória
  (schema inválido, EARS mal-formado, drift estrito) antes que cheguem
  ao histórico, mantendo a memória sempre auditável.
contracts:
  api: src/feat_memory/governance/data/hooks/pre-commit
  tests:
    - tests/test_deploy.py
acceptance:
  - id: A1
    pattern: event
    trigger: "git commit é invocado em projeto com o hook instalado"
    response: "executa feat-memory audit --strict --no-index antes do commit"
  - id: A2
    pattern: unwanted
    trigger: "a auditoria retorna exit 1 (schema inválido ou drift estrito)"
    response: "bloqueia o commit e imprime os problemas detectados"
  - id: A3
    pattern: unwanted
    trigger: "o binário feat-memory não está no PATH"
    response: >
      emite warning com instruções de instalação e libera o commit
      (fail-open) — não bloqueia
  - id: A4
    pattern: ubiquitous
    requirement: "respeita git commit --no-verify como válvula de escape"
depends_on: [F-0002]
decisions: [ADR-0008]
---

# F-0005 · pre-commit-hook

## Comportamento

Hook em [src/feat_memory/governance/data/hooks/pre-commit](src/feat_memory/governance/data/hooks/pre-commit), instalado em `<target>/.git/hooks/pre-commit` pelo deploy (F-0001). Como `.git/` não é versionado, cada clone do projeto consumidor precisa rodar `feat-memory deploy` uma vez para instalar o hook.

Fail-open quando o binário ausente é decisão deliberada (ADR-0008): hooks que falham por estado do ambiente acabam sendo desinstalados por usuários frustrados. Em CI, a auditoria deve rodar como step explícito separado, não confiando apenas no hook.
