---
id: F-0001
name: deploy
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Instala a metodologia agent-memory em qualquer projeto consumidor com
  um único comando idempotente. Preserva conteúdo pré-existente do usuário
  via bloco delimitado por sentinelas markdown na AGENT.md — só o bloco
  é refrescado a cada deploy, todo o resto fica intacto.
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
      cria AGENT.md (com bloco delimitado por sentinelas markdown),
      CLAUDE.md, STATE.md, skills/ e as pastas manifest/features/ e
      decisions/proposals/ no target; instala pre-commit hook se target
      é repositório Git
  - id: A2
    pattern: state
    state: "AGENT.md já existe no target"
    response: >
      refresca o bloco delimitado por sentinelas (`<!-- >>> agent-memory
      >>> -->` ... `<!-- <<< agent-memory <<< -->`) preservando todo o
      resto do conteúdo do arquivo; anexa o bloco se ainda não estiver
      presente
  - id: A3
    pattern: state
    state: "CLAUDE.md ou STATE.md já existem no target"
    response: >
      pula sem mesclar (CLAUDE.md é redirect mínimo, STATE.md é volátil
      por construção)
  - id: A4
    pattern: optional
    feature: "a flag --force for fornecida"
    response: >
      sobrescreve AGENT.md, CLAUDE.md e STATE.md inteiros a partir do
      template, descartando conteúdo do usuário
  - id: A5
    pattern: optional
    feature: "a flag --no-merge for fornecida"
    response: >
      pula AGENT.md e CLAUDE.md existentes sem refrescar o bloco
      (útil em CI onde nenhuma modificação é desejada)
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
decisions: [ADR-0006, ADR-0007, ADR-0011]
---

# F-0001 · deploy

## Comportamento

Subcomando `agent-memory deploy <target>` da CLI, em [src/agent_memory/deploy.py](src/agent_memory/deploy.py). Copia templates de `src/agent_memory/data/` para a raiz do target via `importlib.resources` (funciona em editable install e em wheel). Instala o pre-commit hook em `<target>/.git/hooks/` quando target é repositório Git.

Idempotente em todas as superfícies: o bloco delimitado por sentinelas markdown na `AGENT.md` é refrescado preservando o resto do arquivo; skills são sempre sobrescritas; blocos com sentinelas em `.gitattributes`/`.gitignore` ficam sincronizados. Substituição de `{VERSION}` em templates usa a versão do pacote instalado (lida via `importlib.metadata`).

A partir de v0.4.0, não há mais merge queue para `AGENT.md`/`CLAUDE.md`. O bloco com sentinelas resolve sozinho o caso de re-deploy sobre arquivo customizado, e `CLAUDE.md` (que é só `@AGENT.md`) é deixado quieto se já existe. O diretório `<target>/.agent-memory-deploy/` legado é removido na primeira execução pós-upgrade.
