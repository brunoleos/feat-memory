---
id: F-0006
name: skill-memory-deploy
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Orienta o agente LLM no fluxo de adoção da metodologia, detectando
  automaticamente projeto greenfield versus legacy e conduzindo
  personalização interativa ou gênese retroativa em quatro fases.
contracts:
  api: src/agent_memory/data/skills/memory-deploy/SKILL.md
acceptance:
  - id: A1
    pattern: event
    trigger: >
      usuário pede para instalar/configurar/adotar a metodologia
      (frases como "instale a metodologia neste projeto")
    response: >
      detecta greenfield versus legacy via número de commits, presença
      de código em src/, manifestos de stack, e existência de AGENT.md
  - id: A2
    pattern: state
    state: "projeto classificado como greenfield"
    response: >
      conduz personalização interativa em diálogo curto sobre identidade,
      stack, restrições e foco inicial
  - id: A3
    pattern: state
    state: "projeto classificado como legacy"
    response: >
      conduz gênese retroativa em quatro fases: AGENT.md a partir do
      código, ADRs do git log, Manifest dos entrypoints, STATE inicial
  - id: A4
    pattern: state
    state: "arquivo .agent-memory-deploy/merge-queue existe"
    response: >
      processa cada merge pendente apresentando para revisão humana antes
      de gravar; remove o diretório transiente após resolução
  - id: A5
    pattern: ubiquitous
    requirement: >
      jamais grava artefatos sem aprovação humana — cristalização
      silenciosa de interpretações erradas é o pior erro possível
depends_on: [F-0001, F-0004]
decisions: [ADR-0004]
---

# F-0006 · skill-memory-deploy

## Comportamento

SKILL.md em [src/agent_memory/data/skills/memory-deploy/SKILL.md](src/agent_memory/data/skills/memory-deploy/SKILL.md). Ponto de entrada único para adoção — invoca `agent-memory deploy` (F-0001) na etapa 2 do fluxo, e `agent-memory migrate` (F-0004) na fase 2 do sub-fluxo legacy.

Princípio operacional central: lotes pequenos, revisão crítica. Limite de cinco itens por rodada de aprovação para evitar saturação do revisor. Conteúdo do usuário é sagrado — em qualquer fase de merge, conteúdo pré-existente prevalece sobre template.
