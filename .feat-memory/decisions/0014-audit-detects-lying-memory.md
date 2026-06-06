---
id: ADR-0014
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0011]
related: [ADR-0002, ADR-0008, ADR-0013]
tags: [audit, schema, validation, freshness, dogfooding]
---

# ADR-0014 · Audit detecta memória mentirosa via cross-check + staleness opcional

## Contexto

`validate_state()` validava shape do frontmatter mas não que `active_features`/`active_decisions` apontavam para arquivos existentes. ID órfão é pior que ausência — `memory-bootstrap` materializa só os IDs listados e confia no que está lá. Há também uma classe mais branda: repositório recebeu código nos últimos N dias sem STATE.md ser tocado, sinal de `memory-debrief` esquecido — não dá para cravar como erro (commit pode ser trivial), mas é warning forte.

## Decisão

Duas extensões separadas por nível de confiança:

- **Cross-check (hard, default-on).** `validate_state_crosscheck(state_fm, features, decisions)` exige arquivo para cada `F-NNNN` em `manifest/features/` ou `manifest/archive/` (F-0012), e para cada `ADR-NNNN` em `decisions/`. Severity `error` — bloqueia o hook. Função separada de `validate_state()` porque depende de features/decisions já carregadas; invocada em `run_audit()` após validação individual.
- **Staleness (soft, opt-in via `--check-staleness[=N]`).** `validate_state_freshness(repo_root, days=7)` lê `git log --since`. Se commits no período tocaram "código" (heurística: paths fora dos prefixos `.feat-memory/`, `tests/`, `docs/`, e fora dos paths exatos `README.md`, `CHANGELOG.md`, `METHODOLOGY.md`, `USER_GUIDE.md`, `FUTURE_IMPROVEMENTS.md`, `LICENSE`) e nenhum tocou `STATE.md`, emite warning sugerindo `/memory-debrief`. Não roda no hook por default. Fail-soft fora de Git ou sem commits no período.

Honra ADR-0002 (cross-check é fato → hard; staleness é sinal → soft) e ADR-0008 (staleness opt-in mantém hook fail-open).

## Alternativas rejeitadas

- **Cross-check como warning**: memória mentirosa é exatamente o defeito que esta tool combate; suavizar dissolve o valor.
- **Cross-check opt-in**: maioria não saberia da flag; default-on é o ponto.
- **Staleness como hard**: sinal é correlativo, não dedutivo (commit trivial não exige debrief); hard quebra fluxos legítimos.
- **Staleness via mtime de STATE.md**: mtime não persiste em clones; `git log` é a fonte de verdade.
- **Lista de "code paths" no frontmatter de AGENTS.md já agora**: YAGNI; esperar caso real (ex: monorepo) para justificar.
