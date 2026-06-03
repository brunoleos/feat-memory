---
schema_version: 2
updated_at: '2026-06-03T05:30:00+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0024
active_decisions:
- ADR-0028
blocked_on: null
---

## Current

Constitution enforced (F-0024, ADR-0028, v0.12.0): constraints ganham bloco `check` opcional executado no audit. Conjunto fechado de 5 checkers em governance/constraints.py; dogfood C1/C2 passa; 179 testes verdes. Primeiro passo do posicionamento "ser a melhor camada de constitution do SDD".

## Next

Aguardar feedback. Pendente do mantenedor: reservar nome na PyPI + trusted publisher (v0.11.0); depois commit/push desta v0.12.0. Movimento 2 (interop/export p/ Spec Kit/Cursor) fora de escopo por decisão do mantenedor.

## Recent

| ts | author | features tocadas | summary |
|---|---|---|---|
| 2026-06-03T05:30:00 | claude-opus-4.8 | F-0024 | v0.12.0: constraint-enforcement — checkers declarativos no audit (ADR-0028). Conjunto fechado, dogfood C1/C2, 25 testes novos. |
| 2026-06-03T04:45:24 | claude-opus-4.8 | F-0021,F-0022,F-0023 | v0.11.0: distribuicao PyPI, CI cross-OS, version de ADR formalizado. |
| 2026-06-03T04:01:51 | claude-opus-4.8 | F-0020 | v0.10.0: saneamento de drift + F-0020/ADR-0024. |
| 2026-05-11T04:35:39 | claude-opus-4.7 | F-0019 | v0.9.0: superseded ADRs em pasta separada (F-0019, ADR-0023). |
| 2026-05-04T21:41:04 | claude-opus-4.7 | F-0015 | Sessão entregou F-0010..F-0015: version-meta, audit anti-mentira, archive. |
