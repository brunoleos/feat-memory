---
schema_version: 2
updated_at: '2026-06-07T12:00:00+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0034
active_decisions:
- ADR-0039
blocked_on: null
---

# Estado

## Current

**v1.3.1 — review pré-merge (patch).** Correções do code/doc review (git history, sem feature/ADR — litmus ADR-0035): classifier→`5 - Production/Stable`; `migrate_legacy_layout` captura `OSError` no rename; docstring de `staged_block_reason` cobre o fail-soft de git inacessível. Fecha o ciclo `feat-memory` (v1.0.0 rename/reposição ADR-0036 → v1.1.0 gate doc-sync ADR-0037 → v1.2.0 subagent ADR-0038 → v1.3.0 migração ADR-0039), pronto para fast-forward na main. 232 testes verdes; audit limpo.

## Next

Fast-forward na `main`. **Follow-up descopado (decisão do mantenedor):** B3 auto-pilot opt-in — pre-commit chama `claude -p` headless p/ rodar o debrief e stageiar, re-checando o gate; off por default, falha→bloqueia; não-testável aqui (sem claude headless) → vira issue própria. Ação externa do mantenedor: reservar `feat-memory` na PyPI + trusted publisher (repo GitHub já renomeado para `feat-memory`).

## Recent

| ts | author | features tocadas | summary |
| --- | --- | --- | --- |
| 2026-06-07T12:00:00 | claude-opus-4.8 | — | v1.3.1: correções de review pré-merge (classifier stable, OSError no migrate, docstring fail-soft). |
| 2026-06-06T15:00:00 | claude-opus-4.8 | F-0034 | v1.3.0: deploy auto-migra .agent-memory/→.feat-memory/ (ADR-0039); .claude/ não-código no gate; dogfood do subagent versionado. |
| 2026-06-06T14:00:00 | claude-opus-4.8 | F-0033 | v1.2.0: subagent de governança projetado pelo deploy (ADR-0038) — wrapper que pré-carrega a skill (fonte única), contexto isolado, pede confirmação p/ commitar. |
| 2026-06-06T13:00:00 | claude-opus-4.8 | F-0032 | v1.1.0: gate hard doc-sync no commit (ADR-0037) — bloqueia código sem doc; complementa o soft de ADR-0016. |
| 2026-06-06T12:00:00 | claude-opus-4.8 | — | v1.0.0: rename agent-memory→feat-memory + reposicionamento como doc viva governada (ADR-0036); 1.0 marca maturidade. |
| 2026-06-04T18:00:00 | claude-opus-4.8 | F-0025,F-0031 | v0.15.0: dissolve F-0030 (changelog-feature); guard anti-balde no audit + litmus nas skills (ADR-0035). |
| 2026-06-04T12:00:00 | claude-opus-4.8 | F-0027,F-0028,F-0029 | v0.14.0: DX hardening Tensegrams — schema ref gerada, autoria propõe/aprova (ADR-0032), CLI [path] uniforme (ADR-0033), polish onboarding (ADR-0034). |
| 2026-06-03T17:30:00 | claude-opus-4.8 | F-0025,F-0026 | v0.13.0: onboarding legacy — esqueleto de frontmatter + STATE freshness (ADR-0029); gênese code-first + migrate agnóstico (ADR-0030). 9 testes novos. |
| 2026-06-03T05:30:00 | claude-opus-4.8 | F-0024 | v0.12.0: constraint-enforcement — checkers declarativos no audit (ADR-0028). Conjunto fechado, dogfood C1/C2, 25 testes novos. |
| 2026-06-03T04:45:24 | claude-opus-4.8 | F-0021,F-0022,F-0023 | v0.11.0: distribuicao PyPI, CI cross-OS, version de ADR formalizado. |

_Histórico anterior a v0.11.0 nos checkpoints (`.feat-memory/checkpoints/`)._
