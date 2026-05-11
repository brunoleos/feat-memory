---
id: F-0009
name: skill-memory-pull-brief
status: in_progress
introduced: 2026-04-30
version: 0.5.0
user_value: Após git pull, brifa o desenvolvedor sobre mudanças trazidas em features/decisions/bloco metodológico do AGENTS.md e propõe ajustes no STATE.md — sem reverter trabalho de colegas em manifest/ e decisions/.
contracts:
  api: src/agent_memory/data/skills/memory-pull-brief/SKILL.md
acceptance:
  - {id: A1, pattern: event, trigger: "usuário pede brief pós-pull (\"o que veio do pull\", \"ressincroniza STATE\")", response: "lista arquivos tocados em manifest/features/, decisions/, e bloco sentinela de AGENTS.md no range @{1}..HEAD"}
  - {id: A2, pattern: event, trigger: "mudanças semânticas extraídas (status, version, supersedes, affects_features)", response: "cruza com STATE.md::active_*, propõe remoção de IDs cuja semântica upstream invalida o foco local, e atualiza Recent"}
  - {id: A3, pattern: ubiquitous, requirement: "nunca modifica arquivos em manifest/ ou decisions/ — só ajusta STATE.md local"}
  - {id: A4, pattern: unwanted, trigger: "branch local tem commits após pull (range ambíguo)", response: "pede base explícita; não chuta"}
  - {id: A5, pattern: state, state: "pull não tocou artefatos da metodologia", response: "encerra em uma frase sem invocar briefing"}
depends_on: [F-0002, F-0007]
decisions: [ADR-0004, ADR-0012]
---

# F-0009 · skill-memory-pull-brief

Espelho de memory-debrief em direção contrária. STATE.md upstream é ignorado por design — `merge=ours` no .gitattributes descarta silenciosamente, então reportar daria informação enganosa.
