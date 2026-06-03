---
id: F-0010
name: version-meta
status: shipped
introduced: 2026-05-03
version: 0.6.0
user_value: Expõe a versão do agent-memory ao consumidor via `--version` no CLI e via `.agent-memory/.meta.yaml`, habilitando audit cross-version (F-0011), telemetria (F-0014) e notice (F-0018).
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
  - {id: A1, pattern: event, trigger: "`agent-memory --version` invocado", response: "imprime `agent-memory X.Y.Z` e sai 0, sem exigir subcomando"}
  - {id: A2, pattern: event, trigger: "`agent-memory deploy <target>` bem-sucedido", response: "grava `<target>/.agent-memory/.meta.yaml` com schema_version, version, deployed_at, cli_path, telemetry_enabled"}
  - {id: A3, pattern: state, state: "`.meta.yaml` existe", response: "`read_meta(root)` retorna o dict; campos faltantes não disparam exceção"}
  - {id: A4, pattern: unwanted, trigger: "`.meta.yaml` ausente (consumidor pré-v0.6)", response: "`read_meta` retorna `None`; chamadores degradam graciosamente"}
  - {id: A5, pattern: ubiquitous, requirement: "`deploy_meta()` é idempotente — re-deploy sobrescreve sem flag adicional"}
depends_on: [F-0001]
decisions: [ADR-0013]
---

# F-0010 · version-meta

`.meta.yaml` é versionado no Git do consumidor — metadata de instalação paralela a `package.json`/`pyproject.toml`, não memória de projeto.
