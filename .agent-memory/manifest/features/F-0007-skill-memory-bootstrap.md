---
id: F-0007
name: skill-memory-bootstrap
status: shipped
introduced: 2026-04-28
version: 0.5.0
user_value: >
  Orienta o agente LLM no início de cada sessão a carregar contexto
  eficientemente sem violar o orçamento de retomada, e a apresentar
  briefing tático antes de prosseguir com a tarefa. Quando detecta
  merge que tocou artefatos da metodologia, delega para memory-pull-brief
  antes do briefing.
contracts:
  api: src/agent_memory/memory/data/skills/memory-bootstrap/SKILL.md
acceptance:
  - id: A1
    pattern: event
    trigger: >
      usuário pergunta sobre estado atual do projeto (frases como
      "onde paramos", "qual o status", "carregue o contexto")
    response: >
      carrega STATE.md, manifest/INDEX.md e decisions/INDEX.md em
      sequência
  - id: A2
    pattern: ubiquitous
    requirement: >
      respeita o orçamento resumption_max_bytes definido em
      AGENT.md::budgets — não expande Manifest inteiro nem todos os ADRs
  - id: A3
    pattern: event
    trigger: "o carregamento inicial conclui"
    response: >
      expande apenas as features e ADRs listados em
      STATE.md::active_features e STATE.md::active_decisions, e apresenta
      briefing tático curto antes de prosseguir
  - id: A4
    pattern: state
    state: >
      último commit é merge que tocou manifest/features/, decisions/, ou
      o bloco entre sentinelas de AGENT.md
    response: >
      delega para skill memory-pull-brief (F-0009) antes do briefing
      tático, deixando STATE.md consistente com a nova realidade upstream
depends_on: []
decisions: [ADR-0004, ADR-0012]
---

# F-0007 · skill-memory-bootstrap

## Comportamento

SKILL.md em [src/agent_memory/memory/data/skills/memory-bootstrap/SKILL.md](src/agent_memory/memory/data/skills/memory-bootstrap/SKILL.md). A skill mais barata em frequência de uso — ativa no início de cada sessão. Eficiência de carga é o objetivo principal: STATE + dois índices cabem em poucos KB e dão ao agente a posição inicial sem reler todo o repositório.
