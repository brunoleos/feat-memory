---
schema_version: 2
updated_at: '2026-06-06T15:00:00+00:00'
updated_by: claude-opus-4.8
active_features:
- F-0034
active_decisions:
- ADR-0039
blocked_on: null
---

# Estado

## Current

**v1.3.0 — migração de consumidores + refino do subagent.** O `deploy` auto-migra o layout legado `.agent-memory/`→`.feat-memory/` (F-0034, ADR-0039) — idempotente, não-destrutivo, limpa transiente e avisa (reinstalar hook + `pipx uninstall agent-memory`): upgrade de um comando para quem vinha de `agent-memory`. Refino: `.claude/` virou não-código no gate doc-sync (specs de subagent são metodologia, não produto); `deploy_agents` avisa a versionar `.claude/agents/`; `.gitignore` deste repo passou a `.claude/*` + `!.claude/agents/`, versionando o próprio subagent (dogfood real, corrigindo a v1.2.0 onde ele ficava gitignored). 231 testes verdes (4 novos), audit limpo. Núcleo do plano feat-memory entregue: v1.0.0 rename/reposição (ADR-0036), v1.1.0 gate doc-sync (ADR-0037), v1.2.0 subagent (ADR-0038), v1.3.0 migração (ADR-0039).

## Next

Abrir PR da branch `feat/rename-feat-memory-governance-agent`. **Follow-up descopado deste ciclo (decisão do mantenedor):** B3 auto-pilot opt-in — pre-commit chama `claude -p`/Agent SDK headless para rodar o debrief e stageiar, re-checando o gate; off por default, falha→bloqueia. Não-testável no ambiente atual (sem claude headless), por isso vira issue própria. Cleanup pendente: reinstalar pipx p/ 1.3.0 + bumpar `.meta.yaml`. Ação do mantenedor (externa): reservar `feat-memory` na PyPI + trusted publisher; renomear repo GitHub `brunoleos/agent-memory`→`feat-memory`.

## Recent

| ts | author | features tocadas | summary |
| --- | --- | --- | --- |
| 2026-06-06T15:00:00 | claude-opus-4.8 | F-0034 | v1.3.0: deploy auto-migra .agent-memory/→.feat-memory/ (ADR-0039); .claude/ não-código no gate; dogfood do subagent versionado. |
| 2026-06-06T14:00:00 | claude-opus-4.8 | F-0033 | v1.2.0: subagent de governança projetado pelo deploy (ADR-0038) — wrapper que pré-carrega a skill (fonte única), contexto isolado, pede confirmação p/ commitar. |
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
