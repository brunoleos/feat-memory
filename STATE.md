---
schema_version: 2
updated_at: 2026-04-30T08:31:50Z
updated_by: claude-opus-4.7
active_features: [F-0006]
active_decisions: [ADR-0010]
blocked_on: null
---

## Current

Refactor da skill `memory-deploy` para corrigir bug de concatenação no merge do `AGENT.md`. Template agora carrega só seções de metodologia (intro, Skills, Como retomar); seções de projeto (Identidade, Restrições, Convenções) são escritas pela skill durante personalização. Etapa 3 reescrita com algoritmo determinístico baseado em listas fixas. F-0006 atualizado (novo critério A6 + template adicionado aos contracts). ADR-0010 em `decisions/proposals/` aguardando aprovação.

## Next

Aprovar ADR-0010 (mover de `proposals/` para `decisions/0010-merge-separates-methodology-from-project-sections.md`) e commitar a sessão.

## Recent

| ts         | agent            | features touched | summary                                                              |
|------------|------------------|------------------|----------------------------------------------------------------------|
| 2026-04-30 | claude-opus-4.7  | F-0006           | merge AGENT.md: metodologia sync, projeto preservado; ADR-0010       |
| 2026-04-29 | claude-opus-4.7  | F-0001..F-0008   | gênese retroativa via skill memory-deploy: AGENT, 9 ADRs, 8 features |
