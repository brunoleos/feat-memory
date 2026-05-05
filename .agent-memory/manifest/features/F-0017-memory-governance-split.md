---
id: F-0017
name: memory-governance-split
status: in_progress
introduced: 2026-05-05
version: 0.7.0
user_value: >
  Separa arquiteturalmente o pacote em três camadas (shared, memory,
  governance) com regra de dependência hierárquica. Permite ao consumidor
  usar puramente memória sem invocar governança, e ao mantenedor evoluir
  cada camada sem coupling oculto. UX do CLI inalterada (mesmo binário,
  mesmos subcomandos), separação vive na estrutura de código e no --help
  agrupado por categoria.
contracts:
  api:
    - src/agent_memory/shared/paths.py
    - src/agent_memory/shared/parsing.py
    - src/agent_memory/memory/schemas.py
    - src/agent_memory/memory/indexing.py
    - src/agent_memory/governance/audit.py
    - src/agent_memory/cli.py
    - src/agent_memory/deploy.py
  tests:
    - tests/
acceptance:
  - id: A1
    pattern: ubiquitous
    requirement: >
      nenhum módulo de `agent_memory.memory.*` importa de
      `agent_memory.governance.*`; verificável via grep ou ferramenta
      de análise de dependências
  - id: A2
    pattern: ubiquitous
    requirement: >
      `agent_memory.shared.*` não importa nada do projeto (apenas stdlib
      + dependências externas como pyyaml)
  - id: A3
    pattern: event
    trigger: "`agent-memory deploy <target> --no-hooks` é executado"
    response: >
      target recebe artefatos de memória completos (AGENT.md, STATE.md,
      manifest/, decisions/, skills/) sem hook de governança instalado;
      consumidor pode operar puramente em memória
  - id: A4
    pattern: ubiquitous
    requirement: >
      todos os subcomandos pré-existentes da CLI continuam disponíveis
      com mesma interface (--help, flags, comportamento) — refactor é
      Liskov-safe quanto à superfície externa
  - id: A5
    pattern: state
    state: "`agent-memory --help` é invocado"
    response: >
      subcomandos aparecem agrupados por categoria (Memória / Governança)
      via grupos de argparse, deixando a separação visível ao usuário
  - id: A6
    pattern: ubiquitous
    requirement: >
      o pre-commit hook continua invocando `agent-memory audit`,
      `check-staleness-staged`, `check-version-bump-staged` via shell
      sem importar Python — refactor não toca o contrato com Git
  - id: A7
    pattern: ubiquitous
    requirement: >
      a suíte de testes passa com mesmo número (ou maior) de casos
      antes e depois do refactor — comportamento observável idêntico
depends_on: [F-0001, F-0002]
decisions: [ADR-0021]
---

# F-0017 · memory-governance-split

## Comportamento

Reorganiza `src/agent_memory/` em três subpacotes com regra de dependência hierárquica:

```
src/agent_memory/
  shared/      # paths, parsing — sem dependências do projeto
  memory/      # schemas, indexing, archive, checkpoints, propose-adr, migrate, data/templates+skills
  governance/  # audit, telemetry, check-staleness, check-version-bump, install_hooks, data/hooks
  cli.py       # router, agrupa subcomandos por categoria no --help
  deploy.py    # bootstrap, orquestra memory.* + governance.install_hooks
```

**Direção de dependência:** `shared` ⇐ `memory` ⇐ `governance`. `memory` nunca importa `governance`. Verificável mecanicamente.

**Equivalência funcional.** Nenhum subcomando muda nome, flag ou comportamento observável. Pre-commit hook continua chamando os mesmos `agent-memory <subcomando>` via shell. Templates, skills e hook são movidos para os data/ dos subpacotes correspondentes; deploy resolve via `importlib.resources` no novo layout.

**Agrupamento no `--help`.** [src/agent_memory/cli.py](src/agent_memory/cli.py) usa grupos de argparse para apresentar dois grupos:
- **Memória:** `deploy`, `audit`, `propose-adr`, `migrate`, `archive`, `checkpoint`, `state-rebuild`
- **Governança:** `record`, `log`, `check-staleness-staged`, `check-version-bump-staged`

`audit` fica no grupo Memória pelo papel de entrada validacional, mesmo vivendo em `governance/` por orquestrar métricas/drift/freshness.

ADR-0021 explica a política da separação, a direção de dependência e por que escolhemos um pacote / um CLI / três subpacotes (vs. dois pacotes pip ou dois CLIs).
