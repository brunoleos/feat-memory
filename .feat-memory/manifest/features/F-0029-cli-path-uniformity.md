---
id: F-0029
name: cli-path-uniformity
status: shipped
introduced: 2026-06-04
version: 0.14.0
user_value: >
  Interface previsível: deploy, audit e migrate aceitam todos um `[path]`
  posicional opcional com default no diretório atual. `cmd` opera no cwd,
  `cmd <path>` opera no alvo — sem três convenções diferentes e sem o erro
  "unrecognized arguments" do migrate.
contracts:
  api:
    - src/feat_memory/shared/paths.py::_init_paths
    - src/feat_memory/deploy.py::add_subparser
    - src/feat_memory/governance/audit.py::add_subparser
    - src/feat_memory/memory/migrate.py::add_subparser
  tests:
    - tests/test_cli.py
    - tests/test_deploy.py
acceptance:
  - {id: A1, pattern: ubiquitous, requirement: "deploy, audit e migrate aceitam um `[path]` posicional opcional; ausente, resolvem o root via git/cwd"}
  - {id: A2, pattern: event, trigger: "o usuário passa um caminho explícito ao comando", response: "o comando opera nesse projeto (paths._init_paths usa o override)"}
  - {id: A3, pattern: unwanted, trigger: "o usuário passa um caminho ao `migrate`", response: "não falha mais com 'unrecognized arguments' — o caminho é aceito"}
depends_on: []
decisions: [ADR-0033]
---

# F-0029 · cli-path-uniformity

Resolve a fricção nº3: três comandos, três convenções de path (`deploy <target>`
obrigatório, `audit` só cwd, `migrate` quebrava com path). `paths._init_paths` passa a
aceitar um override opcional de root; `deploy` torna o `target` opcional (default cwd);
`audit` e `migrate` ganham `[path]` posicional opcional. Convenção única em toda a CLI.
