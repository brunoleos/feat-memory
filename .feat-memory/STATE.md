---
schema_version: 2
updated_at: '2026-06-06T13:00:00+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0032
active_decisions:
- ADR-0037
blocked_on: null
---

# Estado

## Current

**v1.1.0 — B1 do agente de governança: gate hard de sincronização doc↔código.** Novo `check-doc-sync-staged` (F-0032, ADR-0037) ligado ao pre-commit: bloqueia (exit 1) commit que toca código sem mover nenhum artefato de doc (`.feat-memory/STATE.md`, `manifest/**` ou `decisions/**`). Complementa o soft `check-staleness-staged` (ADR-0016, que segue nudgando p/ STATE); segue o padrão de guard hard em hook fail-open de ADR-0020 (binário-ausente e `--no-verify` seguem valendo). Converte a promessa de "doc sempre sincronizada" (ADR-0036) de disciplina em garantia. 225 testes verdes (10 novos), audit limpo. Antes (v1.0.0): rename `agent-memory`→`feat-memory` + reposicionamento (ADR-0036).

## Next

Continuar o agente de governança: **(B2)** subagent gerador `memory-debrief` — wrapper fino que pré-carrega a skill (fonte única) via `skills:`, projetado pelo `deploy` em `.claude/agents/`; **(B3)** auto-pilot opt-in (`claude -p` headless no hook). Capacidade separada (litmus ADR-0035): migrador de consumidores `.agent-memory/`→`.feat-memory/` (deve reinstalar hook + alertar sobre shim pipx antigo, como exigiu a própria transição deste repo). Coexistir com a memória nativa, sem integração. Ação do mantenedor: reservar `feat-memory` na PyPI + trusted publisher; renomear repo GitHub `brunoleos/agent-memory`→`feat-memory`.

## Recent

| ts | author | features tocadas | summary |
| --- | --- | --- | --- |
| 2026-06-06T13:00:00 | claude-opus-4.8 | F-0032 | v1.1.0: gate hard doc-sync no commit (ADR-0037) — bloqueia código sem doc; complementa o soft de ADR-0016. |
| 2026-06-06T12:00:00 | claude-opus-4.8 | — | v1.0.0: rename agent-memory→feat-memory + reposicionamento como doc viva governada (ADR-0036); 1.0 marca maturidade. |
| 2026-06-04T18:00:00 | claude-opus-4.8 | F-0025,F-0031 | v0.15.0: dissolve F-0030 (changelog-feature); guard anti-balde no audit + litmus nas skills (ADR-0035). |
| 2026-06-04T12:00:00 | claude-opus-4.8 | F-0027,F-0028,F-0029 | v0.14.0: DX hardening Tensegrams — schema ref gerada, autoria propõe/aprova (ADR-0032), CLI [path] uniforme (ADR-0033), polish onboarding (ADR-0034). |
| 2026-06-03T17:30:00 | claude-opus-4.8 | F-0025,F-0026 | v0.13.0: onboarding legacy — esqueleto de frontmatter + STATE freshness (ADR-0029); gênese code-first + migrate agnóstico (ADR-0030). 9 testes novos. |
| 2026-06-03T05:30:00 | claude-opus-4.8 | F-0024 | v0.12.0: constraint-enforcement — checkers declarativos no audit (ADR-0028). Conjunto fechado, dogfood C1/C2, 25 testes novos. |
| 2026-06-03T04:45:24 | claude-opus-4.8 | F-0021,F-0022,F-0023 | v0.11.0: distribuicao PyPI, CI cross-OS, version de ADR formalizado. |
| 2026-06-03T04:01:51 | claude-opus-4.8 | F-0020 | v0.10.0: saneamento de drift + F-0020/ADR-0024. |
| 2026-05-11T04:35:39 | claude-opus-4.7 | F-0019 | v0.9.0: superseded ADRs em pasta separada (F-0019, ADR-0023). |
| 2026-05-04T21:41:04 | claude-opus-4.7 | F-0015 | Sessão entregou F-0010..F-0015: version-meta, audit anti-mentira, archive. |
