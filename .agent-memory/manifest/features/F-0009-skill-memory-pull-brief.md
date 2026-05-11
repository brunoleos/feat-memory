---
id: F-0009
name: skill-memory-pull-brief
status: in_progress
introduced: 2026-04-30
version: 0.5.0
user_value: >
  Orienta o agente LLM, após git pull em projeto cliente, a brifar o
  desenvolvedor sobre mudanças trazidas em features, decisions e bloco
  metodológico de AGENTS.md, e a propor ajustes em STATE.md para refletir
  a nova realidade — sem reverter trabalho de colegas em manifest/ e
  decisions/.
contracts:
  api: src/agent_memory/data/skills/memory-pull-brief/SKILL.md
acceptance:
  - id: A1
    pattern: event
    trigger: >
      usuário pergunta o que veio do remote após pull (frases como
      "o que veio do pull", "brifa as mudanças do main",
      "ressincroniza o STATE com o que veio")
    response: >
      determina o range do pull (default @{1}..HEAD; se reflog não
      indica pull/merge, pede base explícita) e lista arquivos tocados
      em manifest/features/, decisions/, e bloco sentinela de AGENTS.md
  - id: A2
    pattern: event
    trigger: "lista de arquivos tocados extraída"
    response: >
      compara frontmatter antes (via git show) e depois para identificar
      transições semânticas (status, version, supersedes, affects_features)
      em features e ADRs
  - id: A3
    pattern: event
    trigger: "mudanças semânticas extraídas"
    response: >
      cruza com STATE.md::active_features e active_decisions, propõe
      remoção de IDs cuja semântica upstream invalida o foco local
      (status shipped/deprecated, ADR superseded), e adiciona linha
      em Recent resumindo o pull
  - id: A4
    pattern: ubiquitous
    requirement: >
      nunca modifica arquivos em manifest/ ou decisions/ — esses já vieram
      corretos do pull e escrita seria reversão de trabalho de colegas
  - id: A5
    pattern: unwanted
    trigger: >
      branch local tem commits feitos depois do pull (range @{1}..HEAD
      ambíguo)
    response: >
      pede base explícita ao usuário antes de prosseguir; não chuta
  - id: A6
    pattern: state
    state: "pull não tocou artefatos da metodologia"
    response: >
      encerra em uma frase ("Pull não tocou artefatos da metodologia")
      sem invocar briefing nem buffer Recent
  - id: A7
    pattern: event
    trigger: "ajustes em STATE.md aplicados"
    response: >
      roda agent-memory audit --strict para detectar drift entre STATE
      local e artefatos pulled, e surfaceia eventuais inconsistências
depends_on: [F-0002, F-0007]
decisions: [ADR-0004, ADR-0012]
---

# F-0009 · skill-memory-pull-brief

## Comportamento

SKILL.md em [src/agent_memory/data/skills/memory-pull-brief/SKILL.md](src/agent_memory/data/skills/memory-pull-brief/SKILL.md). Espelho de `memory-debrief` (F-0008) em direção contrária: enquanto o debrief reflete o que **eu fiz** na sessão antes do commit, o pull-brief reflete o que **veio do remote** depois do pull. Triggera manualmente por frases do usuário ou por delegação a partir de `memory-bootstrap` (F-0007) quando o último commit é merge que tocou artefatos.

## Limites conhecidos

- O range default `@{1}..HEAD` pode ser ambíguo se o usuário fez commits locais depois do pull. A skill detecta isso via `git reflog -1 --format='%gs'` e pede base explícita.
- `STATE.md` é ignorado no diff por design: o `.gitattributes` da metodologia o marca `merge=ours`, então mudanças upstream são silenciosamente descartadas pelo merge driver. Reportar daria informação enganosa.
- Mudanças no `AGENTS.md` fora do bloco entre sentinelas são reportadas como nota curta sem detalhamento — são autoria do mantenedor humano e merecem atenção dele, não da skill.
