---
id: F-0010
name: version-meta
status: in_progress
introduced: 2026-05-03
version: 0.6.0
user_value: >
  Permite que projetos consumidores e ferramentas externas descubram qual
  versão do agent-memory produziu sua estrutura, sem parsing frágil de URLs
  em AGENT.md. Habilita audit cross-version (F-0011) e telemetria (F-0014)
  a anotarem eventos contra a versão real, e dá ao usuário um
  `agent-memory --version` que funciona como qualquer CLI moderna.
contracts:
  api:
    - src/agent_memory/cli.py::main
    - src/agent_memory/deploy.py::deploy_meta
    - src/agent_memory/governance/audit.py::read_meta
  tests:
    - tests/test_cli.py
    - tests/test_deploy.py
    - tests/test_meta.py
acceptance:
  - id: A1
    pattern: event
    trigger: "`agent-memory --version` é invocado"
    response: >
      imprime a string da versão (ex.: `agent-memory 0.6.0`) e sai com
      exit code 0, sem exigir subcomando
  - id: A2
    pattern: event
    trigger: "`agent-memory deploy <target>` é executado com sucesso"
    response: >
      cria ou sobrescreve `<target>/.agent-memory/.meta.yaml` com os
      campos `schema_version: 1`, `version`, `deployed_at` (ISO 8601 UTC),
      `cli_path` (abspath do executável atual) e `telemetry_enabled: true`
  - id: A3
    pattern: state
    state: "`.agent-memory/.meta.yaml` existe no consumidor"
    response: >
      `audit.read_meta(root)` retorna o dict YAML carregado;
      campos faltantes não disparam exceção
  - id: A4
    pattern: unwanted
    trigger: "`.agent-memory/.meta.yaml` está ausente (consumidor pré-v0.6)"
    response: >
      `audit.read_meta(root)` retorna `None`; chamadores degradam
      graciosamente sem quebrar o fluxo
  - id: A5
    pattern: ubiquitous
    requirement: >
      `deploy_meta()` é idempotente — re-executar `agent-memory deploy`
      sobrescreve `.meta.yaml` com os valores correntes sem duplicar
      conteúdo nem requerer flag adicional
depends_on: [F-0001]
decisions: [ADR-0013]
---

# F-0010 · version-meta

## Comportamento

Adiciona dois mecanismos complementares para expor a versão do `agent-memory` ao consumidor:

1. **Flag `--version` no parser raiz** ([src/agent_memory/cli.py](src/agent_memory/cli.py)): comportamento padrão `argparse` — imprime `agent-memory <__version__>` e sai com 0. Não exige subcomando, satisfaz a UX universal de CLI.

2. **Arquivo `.agent-memory/.meta.yaml`** ([src/agent_memory/deploy.py](src/agent_memory/deploy.py) via nova função `deploy_meta()`): gravado a cada `agent-memory deploy`, contém `schema_version: 1`, `version`, `deployed_at`, `cli_path`, `telemetry_enabled`. Schema definido em ADR-0013.

3. **Helper `read_meta(root)`** ([src/agent_memory/governance/audit.py](src/agent_memory/governance/audit.py)): lê e devolve o dict; retorna `None` se arquivo ausente. Reusado por F-0011 (cross-check) e F-0014 (telemetria).

O `.meta.yaml` é versionado no Git do consumidor — é metadata de instalação, paralelo a `package.json` ou `pyproject.toml`. Re-deploy sobrescreve o arquivo sem flag adicional (idempotente por construção).
