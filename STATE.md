---
schema_version: 2
updated_at: 2026-04-30T10:21:20Z
updated_by: claude-opus-4.7
active_features: [F-0001, F-0006]
active_decisions: [ADR-0011]
blocked_on: null
---

## Current

Refator radical do deploy: a metodologia em `AGENT.md` agora vive dentro de um bloco delimitado por sentinelas markdown (`<!-- >>> agent-memory >>> --> ... <!-- <<< agent-memory <<< -->`). `deploy.py` faz refresh idempotente do bloco; nada fora é tocado. Mecanismo de merge-queue eliminado. Skill `memory-deploy` perde Etapas 3 (merge) e 4 (personalização) inteiras — fica com detectar/deployar/(legacy) gênese de ADRs+Manifest. Template AGENT.md, README, F-0001 e F-0006 atualizados. ADR-0011 reescrito em proposals/ supersedendo ADR-0010 (já marcado como `superseded_by: ADR-0011`). 25 testes passando, audit limpo. CHANGELOG tem entrada `[Unreleased]` com nota de migração 0.3.x → 0.4.0.

## Next

Aprovar ADR-0011 (mover para `decisions/0011-deploy-replaces-agent-md-block-via-sentinels.md`), commitar, e bumpar para `v0.4.0` (breaking change: skill perde superfície, mecanismo de merge-queue removido).

## Recent

| ts         | agent            | features touched | summary                                                              |
|------------|------------------|------------------|----------------------------------------------------------------------|
| 2026-04-30 | claude-opus-4.7  | F-0001, F-0006   | sentinel-block para metodologia em AGENT.md; merge-queue removido    |
| 2026-04-30 | claude-opus-4.7  | F-0006           | deploy não escreve mais corpo da AGENT.md; só frontmatter; ADR-0011  |
| 2026-04-30 | claude-opus-4.7  | F-0006           | merge AGENT.md: metodologia sync, projeto preservado; ADR-0010       |
| 2026-04-29 | claude-opus-4.7  | F-0001..F-0008   | gênese retroativa via skill memory-deploy: AGENT, 9 ADRs, 8 features |
