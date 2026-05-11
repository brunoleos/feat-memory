---
id: F-0006
name: skill-memory-deploy
status: shipped
introduced: 2026-04-28
version: 0.4.0
user_value: >
  Orienta o agente LLM no fluxo de adoção da metodologia: detecta
  greenfield versus legacy, executa o deploy mecânico, e em projetos
  legacy conduz gênese retroativa de ADRs e do Manifest. Não escreve
  no corpo da AGENTS.md fora do bloco com sentinelas — identidade,
  restrições e convenções específicas do projeto são autoria do
  mantenedor humano.
contracts:
  api:
    - src/agent_memory/data/skills/memory-deploy/SKILL.md
    - src/agent_memory/data/templates/AGENTS.md
acceptance:
  - id: A1
    pattern: event
    trigger: >
      usuário pede para instalar/configurar/adotar a metodologia
      (frases como "instale a metodologia neste projeto")
    response: >
      detecta greenfield versus legacy via número de commits, presença
      de código em src/, manifestos de stack, e existência de AGENTS.md
  - id: A2
    pattern: state
    state: "projeto classificado como greenfield"
    response: >
      executa `agent-memory deploy` e encerra; não pergunta sobre
      identidade, stack, restrições nem foco inicial — toda autoria
      de conteúdo específico do projeto é do mantenedor humano
  - id: A3
    pattern: state
    state: "projeto classificado como legacy"
    response: >
      executa `agent-memory deploy` e em seguida conduz gênese retroativa
      em três fases: ADRs do git log via `agent-memory migrate`, Manifest
      dos entrypoints públicos, e STATE.md::Current descrevendo a gênese;
      não escreve em AGENTS.md fora do bloco com sentinelas
  - id: A4
    pattern: ubiquitous
    requirement: >
      jamais escreve no corpo da AGENTS.md fora do bloco delimitado pelas
      sentinelas markdown agent-memory — identidade, restrições e
      convenções específicas do projeto são autoria do mantenedor humano
  - id: A5
    pattern: ubiquitous
    requirement: >
      jamais grava artefatos sem aprovação humana — cristalização
      silenciosa de interpretações erradas é o pior erro possível
depends_on: [F-0001, F-0004]
decisions: [ADR-0004, ADR-0010, ADR-0011]
---

# F-0006 · skill-memory-deploy

## Comportamento

SKILL.md em [src/agent_memory/memory/data/skills/memory-deploy/SKILL.md](src/agent_memory/memory/data/skills/memory-deploy/SKILL.md). Ponto de entrada único para adoção — invoca `agent-memory deploy` (F-0001) na Etapa 2 do fluxo, e `agent-memory migrate` (F-0004) na Fase 3.1 do sub-fluxo legacy.

Princípio operacional central: a skill toca em `decisions/`, `manifest/` e `STATE.md` durante a gênese retroativa, mas nunca no corpo da `AGENTS.md` fora do bloco com sentinelas. O bloco em si é gerenciado pelo `agent-memory deploy` de forma idempotente. Todo conteúdo de projeto na `AGENTS.md` (identidade, restrições, convenções) é autoria humana.

Lotes pequenos, revisão crítica. Limite de cinco itens por rodada de aprovação na gênese de ADRs e features para evitar saturação do revisor.
