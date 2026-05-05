---
id: F-0008
name: skill-memory-debrief
status: shipped
introduced: 2026-04-28
version: 0.3.0
user_value: >
  Orienta o agente LLM ao fechar uma unidade de trabalho a refletir as
  mudanças na memória persistente — atualizar Manifest, reescrever STATE,
  e propor ADR se houver decisão arquitetural não-trivial — antes do commit.
contracts:
  api: src/agent_memory/memory/data/skills/memory-debrief/SKILL.md
acceptance:
  - id: A1
    pattern: event
    trigger: >
      usuário sinaliza intenção de commitar (frases como "vou commitar",
      "atualize o STATE", "antes de subir")
    response: "examina o diff atual via git diff e identifica features tocadas"
  - id: A2
    pattern: event
    trigger: "diff examinado"
    response: >
      atualiza entradas do Manifest para features tocadas (status, version,
      contracts, acceptance conforme apropriado)
  - id: A3
    pattern: event
    trigger: "Manifest atualizado"
    response: >
      reescreve as zonas Current e Next do STATE.md e adiciona uma linha
      em Recent com timestamp e features tocadas
  - id: A4
    pattern: state
    state: "diff contém sinais de decisão arquitetural não-trivial"
    response: >
      invoca agent-memory propose-adr (F-0003) para gerar draft em
      decisions/proposals/ para revisão
depends_on: [F-0003]
decisions: [ADR-0004]
---

# F-0008 · skill-memory-debrief

## Comportamento

SKILL.md em [src/agent_memory/memory/data/skills/memory-debrief/SKILL.md](src/agent_memory/memory/data/skills/memory-debrief/SKILL.md). A skill mais usada no dia-a-dia. Cobre o momento em que o trabalho realizado precisa ser refletido na memória persistente antes de virar commit.

O debrief é parte do trabalho, não opcional — uma sessão sem debrief é trabalho perdido. As três tarefas (Manifest, STATE, ADR opcional) são sequenciais para o agente, mas o usuário aprova cada artefato antes do commit.
