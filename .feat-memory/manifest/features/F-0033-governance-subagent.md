---
id: F-0033
name: governance-subagent
status: shipped
introduced: 2026-06-06
version: 1.2.0
user_value: >
  O deploy projeta um subagent do Claude Code (.claude/agents/memory-debrief.md)
  que roda o debrief em contexto isolado — pré-carregando a skill homônima como
  fonte única da lógica — e pede confirmação antes de commitar, tirando a leitura
  pesada do diff de dentro da conversa principal.
contracts:
  api:
    - src/feat_memory/deploy.py::deploy_agents
  data:
    - src/feat_memory/data/agents/memory-debrief.md
  tests:
    - tests/test_deploy.py
acceptance:
  - {id: A1, pattern: event, trigger: "`feat-memory deploy` roda num projeto", response: "cria `.claude/agents/memory-debrief.md` com frontmatter `name: memory-debrief` e `skills: [memory-debrief]`"}
  - {id: A2, pattern: ubiquitous, requirement: "o subagent é wrapper fino — a lógica vive na skill `memory-debrief` (fonte única), pré-carregada via `skills:`, nunca duplicada no corpo do agente"}
  - {id: A3, pattern: event, trigger: "deploy roda de novo (redeploy)", response: "o arquivo é sobrescrito sem duplicar (conteúdo de metodologia)"}
  - {id: A4, pattern: ubiquitous, requirement: "o corpo do subagent instrui pedir confirmação ao humano antes de commitar e escrever só em `.feat-memory/` (não na memória nativa)"}
depends_on: []
decisions: [ADR-0038]
---

# F-0033 · governance-subagent

Adapter Claude Code do agente de governança. `deploy_agents` projeta a spec canônica
(`data/agents/*.md`, novo package-data) em `.claude/agents/`. O subagent é casca: o
campo `skills:` pré-carrega a skill `memory-debrief`, que continua a **fonte única** da
lógica (ADR-0038) — o wrapper só adiciona a janela isolada (não polui o contexto
principal com a leitura do diff) e as regras de operação (escreve em `.feat-memory/`,
pede confirmação antes de commitar). Núcleo da metodologia segue tool-agnóstico; o
subagent é adapter opcional. Coexiste com a memória nativa do Claude Code, sem integração.
