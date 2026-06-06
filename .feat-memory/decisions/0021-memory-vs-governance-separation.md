---
id: ADR-0021
date: 2026-05-05
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0017]
related: [ADR-0008, ADR-0014, ADR-0016, ADR-0020]
tags: [architecture, separation-of-concerns, refactor, packaging]
---

# ADR-0021 · Separação arquitetural memória × governança em subpacotes

## Contexto

Após v0.6.0, `src/feat_memory/` misturava dois propósitos: memória de agente (AGENTS.md/STATE.md/manifest/decisions/skills, schemas, deploy, ciclo de vida — o agente lê isto) e governança (audit, hooks, telemetria, check-staleness, check-version-bump — enforcement disciplinar). O usuário foi explícito: "A parte de memória do agente é meu foco. Ainda não sei se preciso da governança. Deixe a separação totalmente independente." Sem refactor, quem importa `archive` aprende que precisa de `audit` para regenerar índices; `--no-hooks` em deploy ajuda mas não impede invocação manual de telemetria/check_staleness. A pergunta de design não é "separar?", é "qual a forma".

## Decisão

**Um pacote pip, um CLI, três subpacotes internos com regra de dependência hierárquica:**

- `shared/` — utilitários sem opinião (`paths`, `parsing`); importa só stdlib + pyyaml.
- `memory/` — schemas, indexing, archive, checkpoints, propose-adr, migrate, data/templates+skills. Importa só `shared`.
- `governance/` — audit, telemetry, check-staleness, check-version-bump, version-check, install-hooks, data/hooks. Importa de `shared` e `memory`.
- `cli.py` e `deploy.py` no top-level (orquestradores).

**Memory nunca importa governance.** Regra mecanicamente verificável; torna `deploy --no-hooks` operação puramente memória. Decisões pontuais: `archive` em **memory** (ciclo de vida, não enforcement); `audit` em **governance** mesmo importando `memory.schemas` (schemas são fato, audit decide o que fazer com violações); `deploy.py` top-level (orquestra ambos); **um CLI** com subcomandos agrupados por categoria no `--help` via argparse groups. Refactor toca ~25 arquivos (módulos + testes); zero mudança de contrato externo; testes monkeypatchando `audit.ROOT` precisam migrar para `shared.paths.ROOT`. Pre-commit hook é shell que invoca CLI — agnóstico ao layout interno.

## Alternativas rejeitadas

- **Dois pacotes pip distintos**: mais "totalmente independente" no literal, mas usuário disse para manter `feat-memory deploy` instalando tudo. Caminho fica aberto se um dia justificar.
- **Dois CLIs no mesmo pacote**: consumidor lembraria dois binários; agrupamento argparse atinge 90% do ganho.
- **Manter `audit.py` monolítico só renomeando arquivos**: cosmético; não resolve `archive` chamando `audit.run_audit()`.
- **Refatorar em 1 commit só**: diff impossível de revisar (+1500/-800); granularidade segue disciplina de F-0010..F-0015.
- **Mover `deploy.py` para `memory/`**: também instala hook (governance); top-level é o lugar honesto.
