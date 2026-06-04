---
schema_version: 2
updated_at: '2026-06-04T12:00:00+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0027
- F-0028
- F-0029
- F-0030
active_decisions:
- ADR-0032
- ADR-0033
- ADR-0034
blocked_on: null
---

# Estado

## Current

DX hardening da adoção legacy (v0.14.0), a partir do relatório de uso da Tensegrams. F-0027/schema-reference: `agent-memory schema` imprime referência gerada de `schemas.py` (campos, EARS, enums) — fim da necessidade de ler o código-fonte; doc espelho com teste de sincronia. F-0028/frontmatter-authorship (ADR-0032): reconcilia a contradição "skill proíbe escrever × comentário manda preencher" — agente propõe project/stack/constraints de evidência, humano aprova. F-0029/cli-path-uniformity (ADR-0033): deploy/audit/migrate aceitam `[path]` opcional (default cwd). F-0030/legacy-onboarding-polish (ADR-0034): guard de upgrade (schema 0.00→re-deploy), meta sem cli_path, budget morto removido, STATE passa MD lint, dedup SKILL↔AGENTS, paths nativos. ~205 testes verdes; audit schema 1.00.

## Next

Aguardar feedback. Pendente do mantenedor: reservar nome na PyPI + trusted publisher; depois commit/push das v0.12.0–v0.14.0 acumuladas. Movimento 2 (interop/export p/ Spec Kit/Cursor) fora de escopo por decisão do mantenedor.

## Recent

| ts | author | features tocadas | summary |
| --- | --- | --- | --- |
| 2026-06-04T12:00:00 | claude-opus-4.8 | F-0027,F-0028,F-0029,F-0030 | v0.14.0: DX hardening Tensegrams — schema ref gerada, autoria propõe/aprova (ADR-0032), CLI [path] uniforme (ADR-0033), polish onboarding (ADR-0034). |
| 2026-06-03T17:30:00 | claude-opus-4.8 | F-0025,F-0026 | v0.13.0: onboarding legacy — esqueleto de frontmatter + STATE freshness (ADR-0029); gênese code-first + migrate agnóstico (ADR-0030). 9 testes novos. |
| 2026-06-03T05:30:00 | claude-opus-4.8 | F-0024 | v0.12.0: constraint-enforcement — checkers declarativos no audit (ADR-0028). Conjunto fechado, dogfood C1/C2, 25 testes novos. |
| 2026-06-03T04:45:24 | claude-opus-4.8 | F-0021,F-0022,F-0023 | v0.11.0: distribuicao PyPI, CI cross-OS, version de ADR formalizado. |
| 2026-06-03T04:01:51 | claude-opus-4.8 | F-0020 | v0.10.0: saneamento de drift + F-0020/ADR-0024. |
| 2026-05-11T04:35:39 | claude-opus-4.7 | F-0019 | v0.9.0: superseded ADRs em pasta separada (F-0019, ADR-0023). |
| 2026-05-04T21:41:04 | claude-opus-4.7 | F-0015 | Sessão entregou F-0010..F-0015: version-meta, audit anti-mentira, archive. |
