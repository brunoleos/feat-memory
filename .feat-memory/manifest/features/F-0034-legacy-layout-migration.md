---
id: F-0034
name: legacy-layout-migration
status: shipped
introduced: 2026-06-06
version: 1.3.0
user_value: >
  O deploy detecta e migra automaticamente o layout legado .agent-memory/ →
  .feat-memory/, dando aos consumidores que adotaram a metodologia como
  agent-memory um caminho de upgrade de um comando, idempotente e não-destrutivo.
contracts:
  api:
    - src/feat_memory/deploy.py::migrate_legacy_layout
  tests:
    - tests/test_deploy.py
acceptance:
  - {id: A1, pattern: event, trigger: "`feat-memory deploy` roda num projeto com `.agent-memory/` e sem `.feat-memory/`", response: "o diretório é renomeado para `.feat-memory/` e o deploy segue (reinstala hook, refresca AGENTS.md)"}
  - {id: A2, pattern: unwanted, trigger: "`.agent-memory/` e `.feat-memory/` coexistem", response: "não sobrescreve — avisa e deixa o legado para reconciliação manual"}
  - {id: A3, pattern: ubiquitous, requirement: "idempotente: sem `.agent-memory/`, é no-op (retorna False)"}
  - {id: A4, pattern: event, trigger: "existe o transiente legado `.agent-memory-deploy/`", response: "é removido durante a migração"}
depends_on: []
decisions: [ADR-0039]
---

# F-0034 · legacy-layout-migration

Caminho de upgrade para o rename do ADR-0036. `migrate_legacy_layout` roda no início do
`deploy`: renomeia `.agent-memory/`→`.feat-memory/` (preserva conteúdo), é idempotente e
não-destrutivo (não clobbera um `.feat-memory/` existente), limpa o transiente legado e
emite avisos acionáveis (reinstalar hook — que o deploy já faz — e `pipx uninstall
agent-memory`). Cobre o rename de diretório, que é o que a CLI precisa para voltar a
funcionar; prosa interna do consumidor não é reescrita (cosmético). Acompanha o refino de
tratar `.claude/` como não-código no gate doc-sync (specs de subagent são metodologia).
