---
schema_version: 2
updated_at: '2026-06-04T18:00:00+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0025
- F-0031
active_decisions:
- ADR-0035
blocked_on: null
---

# Estado

## Current

Correção de Manifest + blindagem (v0.15.0). F-0030 era uma feature guarda-chuva/changelog (6 mudanças sem relação num arquivo) — **dissolvida**: o guard de upgrade dobrou no F-0025 (mesma capacidade, +A6); o resto (budget, cli_path, lint, dedup, paths) é git history + ADR-0034. Para não reincidir, prevenção em camadas (ADR-0035, F-0031): (1) mecânica — `validate_feature` bloqueia `error` nomes-balde via `CHANGELOG_NAME_WORDS` (teria pego "legacy-onboarding-polish"); (2) doutrinária — "Teste de uma capacidade" nas skills memory-debrief e memory-deploy; (3) não-cobertura honesta — sem cohesion-checker (ruidoso, mentiria; ADR-0014). Suíte verde; audit schema 1.00.

## Next

Aguardar feedback. Pendente do mantenedor: reservar nome na PyPI + trusted publisher; depois commit/push das v0.12.0–v0.15.0 acumuladas. Movimento 2 (interop/export p/ Spec Kit/Cursor) fora de escopo por decisão do mantenedor.

## Recent

| ts | author | features tocadas | summary |
| --- | --- | --- | --- |
| 2026-06-04T18:00:00 | claude-opus-4.8 | F-0025,F-0031 | v0.15.0: dissolve F-0030 (changelog-feature); guard anti-balde no audit + litmus nas skills (ADR-0035). |
| 2026-06-04T12:00:00 | claude-opus-4.8 | F-0027,F-0028,F-0029 | v0.14.0: DX hardening Tensegrams — schema ref gerada, autoria propõe/aprova (ADR-0032), CLI [path] uniforme (ADR-0033), polish onboarding (ADR-0034). |
| 2026-06-03T17:30:00 | claude-opus-4.8 | F-0025,F-0026 | v0.13.0: onboarding legacy — esqueleto de frontmatter + STATE freshness (ADR-0029); gênese code-first + migrate agnóstico (ADR-0030). 9 testes novos. |
| 2026-06-03T05:30:00 | claude-opus-4.8 | F-0024 | v0.12.0: constraint-enforcement — checkers declarativos no audit (ADR-0028). Conjunto fechado, dogfood C1/C2, 25 testes novos. |
| 2026-06-03T04:45:24 | claude-opus-4.8 | F-0021,F-0022,F-0023 | v0.11.0: distribuicao PyPI, CI cross-OS, version de ADR formalizado. |
| 2026-06-03T04:01:51 | claude-opus-4.8 | F-0020 | v0.10.0: saneamento de drift + F-0020/ADR-0024. |
| 2026-05-11T04:35:39 | claude-opus-4.7 | F-0019 | v0.9.0: superseded ADRs em pasta separada (F-0019, ADR-0023). |
| 2026-05-04T21:41:04 | claude-opus-4.7 | F-0015 | Sessão entregou F-0010..F-0015: version-meta, audit anti-mentira, archive. |
