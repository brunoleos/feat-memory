---
schema_version: 2
updated_at: '2026-06-25T22:48:59+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0034
active_decisions:
- ADR-0040
blocked_on: null
---

# Estado

## Current

**v1.4.0 — supersede parcial (ADR-0040).** Regra de governança nova: quando uma decisão invalida só **parte** de um ADR, marca-se o base inteiro como `superseded` e divide-se em ADRs novos (a novidade + a parte mantida), com `superseded_by` listando todos os sucessores — todo ADR vigente passa a ser verdadeiro por inteiro. Documentada no skill `memory-debrief` (§4) e em METHODOLOGY §4; sem mudança de código (o schema já aceitava `superseded_by` em lista). 232 testes verdes; audit limpo.

## Next

Publicar 1.4.0: `git push` + tag `v1.4.0` quando aprovado. **Follow-ups descopados (mantenedor):** (1) B3 auto-pilot opt-in — pre-commit chama `claude -p` headless p/ rodar o debrief e stageiar; off por default, falha→bloqueia; vira issue própria. (2) Reservar `feat-memory` na PyPI + trusted publisher. **Dívida de processo:** checkpoints/ parou em v0.11.0 — STATE foi mantido à mão de v0.12.0→v1.3.1; `state-rebuild` regenera só da cadeia de checkpoints e perde esse histórico. Decidir se backfilla checkpoints ou aposenta o mecanismo.

## Recent

| ts | author | features tocadas | summary |
| --- | --- | --- | --- |
| 2026-06-25T22:48:00 | claude-opus-4.8 | — | v1.4.0: supersede parcial (ADR-0040) — base→superseded total + split em ADRs novos; doc-only, schema já aceita lista. |
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
