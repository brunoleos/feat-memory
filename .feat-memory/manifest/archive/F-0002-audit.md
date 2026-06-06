---
id: F-0002
name: audit
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Valida estrutura de todos os artefatos de memória, detecta drift entre
  Manifest e código, e gera índices automaticamente — produzindo um
  relatório de saúde que orienta manutenção.
contracts:
  api: src/feat_memory/governance/audit.py::run
  tests:
    - tests/test_cli.py
    - tests/test_entrypoint.py
acceptance:
  - id: A1
    pattern: event
    trigger: "feat-memory audit é invocado"
    response: >
      valida schemas de AGENTS.md, STATE.md, features em manifest/ e ADRs
      em decisions/, incluindo notação EARS de cada acceptance criterion
  - id: A2
    pattern: ubiquitous
    requirement: >
      sem a flag --no-index, regenera manifest/INDEX.md e
      decisions/INDEX.md ao final da auditoria
  - id: A3
    pattern: optional
    feature: "a flag --strict for fornecida"
    response: "drift no Manifest é promovido de warning a error (exit 1)"
  - id: A4
    pattern: optional
    feature: "a flag --json for fornecida"
    response: "emite saída estruturada JSON em vez de relatório textual"
  - id: A5
    pattern: optional
    feature: "a flag --no-index for fornecida"
    response: "pula geração dos arquivos INDEX.md (validação apenas)"
  - id: A6
    pattern: unwanted
    trigger: "PyYAML não está instalado no ambiente"
    response: >
      sai com exit 1 e mensagem acionável listando opções de instalação
      (pip, pip3, --break-system-packages, virtualenv)
  - id: A7
    pattern: ubiquitous
    requirement: >
      retorna exit 0 quando não há erros, exit 1 quando há erro de schema
      ou drift em modo --strict
depends_on: []
decisions: [ADR-0002, ADR-0003]
---

# F-0002 · audit

## Comportamento

Subcomando `feat-memory audit` da CLI, em [src/feat_memory/governance/audit.py](src/feat_memory/governance/audit.py). Descobre o project root via `git rev-parse --show-toplevel` (com fallback para CWD) e valida os quatro artefatos.

O relatório padrão lista sete indicadores: conformidade de schema, custo de retomada, frescor de estado, cobertura do manifest, drift do manifest, velocity de features `in_progress`, e saúde de decisões (razão de substituição). PyYAML é importado preguiçosamente — `feat-memory --help` não paga o custo de carregá-lo.

Em modo `--strict`, drift detectado bloqueia a saída. Modo padrão emite warning. O pre-commit hook (F-0005) usa `--strict --no-index` para não regenerar índices em cada commit.
