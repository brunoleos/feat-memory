---
id: F-0001
name: deploy
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Instala a metodologia agent-memory em qualquer projeto consumidor com
  um único comando idempotente, preservando customizações pré-existentes
  via merge controlado.
contracts:
  api: src/agent_memory/deploy.py::run
  tests:
    - tests/test_deploy.py
    - tests/test_sentinel.py
    - tests/test_cli.py
    - tests/test_entrypoint.py
acceptance:
  - id: A1
    pattern: event
    trigger: "agent-memory deploy <target> é invocado"
    response: >
      copia AGENT.md, CLAUDE.md, STATE.md, skills/ e cria pastas
      manifest/features/ e decisions/proposals/ no target; instala
      pre-commit hook se target é repositório Git
  - id: A2
    pattern: state
    state: "AGENT.md ou CLAUDE.md já existem no target"
    response: >
      registra em <target>/.agent-memory-deploy/merge-queue para a skill
      memory-deploy resolver, sem sobrescrever
  - id: A3
    pattern: state
    state: "STATE.md já existe no target"
    response: "pula sem mesclar (conteúdo é volátil por construção)"
  - id: A4
    pattern: optional
    feature: "a flag --force for fornecida"
    response: "sobrescreve AGENT/CLAUDE/STATE sem registrar merge queue"
  - id: A5
    pattern: optional
    feature: "a flag --no-merge for fornecida"
    response: "pula AGENT/CLAUDE existentes sem mesclar nem sobrescrever"
  - id: A6
    pattern: optional
    feature: "a flag --no-hooks for fornecida"
    response: "pula instalação do pre-commit hook"
  - id: A7
    pattern: unwanted
    trigger: "target não é repositório Git"
    response: "pula instalação do hook com aviso, mas continua o restante do deploy"
  - id: A8
    pattern: ubiquitous
    requirement: >
      blocos com sentinelas em .gitattributes e .gitignore devem ser
      idempotentes — re-rodar deploy não duplica entradas
depends_on: []
decisions: [ADR-0006, ADR-0007]
---

# F-0001 · deploy

## Comportamento

Subcomando `agent-memory deploy <target>` da CLI, em [src/agent_memory/deploy.py](src/agent_memory/deploy.py). Copia templates de `src/agent_memory/data/` para a raiz do target via `importlib.resources` (funciona em editable install e em wheel). Instala o pre-commit hook em `<target>/.git/hooks/` quando target é repositório Git.

Idempotente: re-rodar atualiza skills (sempre refrescadas), mantém os blocos com sentinelas em `.gitattributes`/`.gitignore` sincronizados, e preserva customizações em `AGENT.md`/`CLAUDE.md` registrando-os para merge pela skill `memory-deploy`. Substituição de `{VERSION}` em templates usa a versão do pacote instalado (lida via `importlib.metadata`).

## Estado transiente

Quando há merges pendentes, o deploy escreve handoff em `<target>/.agent-memory-deploy/{merge-queue,pending/}` (gitignored). A skill `memory-deploy` lê esses arquivos para conduzir o merge e remove o diretório após resolução.
