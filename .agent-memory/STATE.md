---
schema_version: 2
updated_at: '2026-06-03T17:30:00+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0025
- F-0026
active_decisions:
- ADR-0029
- ADR-0030
- ADR-0031
blocked_on: null
---

## Current

Onboarding legacy endurecido (v0.13.0), a partir de feedback da adoção em D:\Projetos\tensegrams. (F-0025/ADR-0029) deploy injeta esqueleto de frontmatter em AGENTS.md em prosa sem frontmatter — antes a auditoria pós-deploy dava conformidade 0.00 e mandava "editar frontmatter" inexistente; bugfix companheiro: STATE.md nasce com `{DEPLOY_DATE}` real (fim do falso-alarme de frescor). (F-0026/ADR-0030+ADR-0031) gênese retroativa vira engenharia reversa multi-fonte code-first: skill memory-deploy Etapa 3 ranqueia fontes por precisão (testes → telas → docs → código → deps → git) com técnicas anti-alucinação (triangulação, confiança em camadas, cobertura=importância); `migrate` agnóstico de linguagem ganha `detect_test_signals`/`detect_ui_signals` além de entrypoints e reordena o output. 191 testes verdes; audit schema 1.00, constraints ok.

## Next

Aguardar feedback. Pendente do mantenedor: reservar nome na PyPI + trusted publisher; depois commit/push das v0.12.0 e v0.13.0 acumuladas. Movimento 2 (interop/export p/ Spec Kit/Cursor) fora de escopo por decisão do mantenedor.

## Recent

| ts | author | features tocadas | summary |
|---|---|---|---|
| 2026-06-03T17:30:00 | claude-opus-4.8 | F-0025,F-0026 | v0.13.0: onboarding legacy — esqueleto de frontmatter + STATE freshness (ADR-0029); gênese code-first + migrate agnóstico (ADR-0030). 9 testes novos. |
| 2026-06-03T05:30:00 | claude-opus-4.8 | F-0024 | v0.12.0: constraint-enforcement — checkers declarativos no audit (ADR-0028). Conjunto fechado, dogfood C1/C2, 25 testes novos. |
| 2026-06-03T04:45:24 | claude-opus-4.8 | F-0021,F-0022,F-0023 | v0.11.0: distribuicao PyPI, CI cross-OS, version de ADR formalizado. |
| 2026-06-03T04:01:51 | claude-opus-4.8 | F-0020 | v0.10.0: saneamento de drift + F-0020/ADR-0024. |
| 2026-05-11T04:35:39 | claude-opus-4.7 | F-0019 | v0.9.0: superseded ADRs em pasta separada (F-0019, ADR-0023). |
| 2026-05-04T21:41:04 | claude-opus-4.7 | F-0015 | Sessão entregou F-0010..F-0015: version-meta, audit anti-mentira, archive. |
