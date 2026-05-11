---
id: F-0007
name: skill-memory-bootstrap
status: shipped
introduced: 2026-04-28
version: 0.5.0
user_value: Orienta o agente a carregar contexto eficientemente no início de cada sessão e a delegar para memory-pull-brief quando o último commit é merge que tocou artefatos da metodologia.
contracts:
  api: src/agent_memory/data/skills/memory-bootstrap/SKILL.md
acceptance:
  - {id: A1, pattern: event, trigger: "usuário pergunta status do projeto (\"onde paramos\", \"carregue contexto\")", response: "carrega STATE.md + manifest/INDEX.md + decisions/INDEX.md"}
  - {id: A2, pattern: ubiquitous, requirement: "respeita resumption_max_bytes de AGENTS.md::budgets; só expande features/ADRs em STATE.md::active_*"}
  - {id: A3, pattern: event, trigger: "carregamento conclui", response: "apresenta briefing tático curto antes de prosseguir"}
  - {id: A4, pattern: state, state: "último commit é merge que tocou manifest/features/, decisions/, ou bloco entre sentinelas de AGENTS.md", response: "delega para memory-pull-brief antes do briefing"}
depends_on: []
decisions: [ADR-0004, ADR-0012]
---
