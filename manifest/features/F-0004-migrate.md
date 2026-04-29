---
id: F-0004
name: migrate
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Em projetos legados, examina o histórico Git e propõe ADRs candidatos +
  detecta a stack principal, materializando matéria-prima para a gênese
  retroativa conduzida pela skill memory-deploy.
contracts:
  api: src/agent_memory/migrate.py::run
  tests:
    - tests/test_cli.py
    - tests/test_entrypoint.py
acceptance:
  - id: A1
    pattern: event
    trigger: "agent-memory migrate é invocado"
    response: >
      examina os últimos N commits (default 100) e detecta candidatos a
      ADR via padrões em mensagens de commit + detecta a stack principal
      via arquivos de manifesto
  - id: A2
    pattern: ubiquitous
    requirement: >
      nunca escreve nenhum arquivo automaticamente — todas as sugestões
      são impressas em stdout para revisão humana
  - id: A3
    pattern: optional
    feature: "a flag --limit N for fornecida"
    response: "examina os últimos N commits em vez do default 100"
  - id: A4
    pattern: optional
    feature: "a flag --json for fornecida"
    response: "emite saída estruturada JSON em vez de relatório textual"
depends_on: []
decisions: []
---

# F-0004 · migrate

## Comportamento

Subcomando `agent-memory migrate` da CLI, em [src/agent_memory/migrate.py](src/agent_memory/migrate.py). Padrões de detecção em mensagens de commit incluem: revert, "instead of", "switched from", "decided to", "replaced X with", "migrated from", "deprecated", "removed X support".

Stacks detectadas pela presença de manifestos: Python (pyproject, setup.py, requirements, Pipfile), Node.js/TypeScript (package.json, tsconfig.json), Rust (Cargo.toml), Go (go.mod), entre outros.

A invariante de "nunca escreve automaticamente" é o que torna a tool segura para projetos legados — gênese silenciosa cristaliza interpretações erradas como decisões oficiais. A skill `memory-deploy` na fase 2 do fluxo legacy invoca esta ferramenta e conduz revisão humana de cada candidato.
