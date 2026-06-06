---
id: ADR-0012
date: 2026-04-30
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0009]
related: [ADR-0004, ADR-0011]
tags: [skills, methodology, post-pull, surface]
---

# ADR-0012 · Skill `memory-pull-brief` cobre o gap cognitivo pós-pull

## Contexto

Três skills cobriam três momentos (instalar, iniciar sessão, fechar unidade). Faltava o quarto: **logo depois de `git pull` em projeto cliente que recebeu commits de colegas**. Os artefatos chegam atualizados mecanicamente, mas há gap cognitivo — `STATE.md::active_*` pode referenciar IDs cuja semântica mudou upstream (feature marcada `shipped`, ADR `superseded`). Proposta anterior via post-merge hook + merge-queue ficou obsoleta com ADR-0011.

## Decisão

Quarta skill `memory-pull-brief`, espelho de `memory-debrief` em direção contrária: revisa o que veio do remote, brifa sobre mudanças semânticas em features/decisions, propõe ajustes no STATE.md local. **Read-only sobre `manifest/` e `decisions/`** — já vieram corretos do pull, escrever neles reverteria trabalho de colegas. Trigger duplo: manual (frases do usuário) e por delegação a partir de `memory-bootstrap` quando o último commit é merge que tocou artefatos. Sem subcomando CLI novo — lógica procedural na SKILL.md usando `git` e `feat-memory audit` direto. Range default `@{1}..HEAD` com detecção via `git reflog` e fallback para base explícita quando ambíguo.

## Alternativas rejeitadas

- **Post-merge git hook automático**: obsoleto com ADR-0011 (templates não chegam por `git pull` em consumidores — chegam por `pipx upgrade`).
- **Subcomando CLI `feat-memory pull-brief`**: lógica é mostly procedural; nenhum valor mecânico justifica binário. Skill mantém superfície CLI enxuta.
- **Auto-aplicar ajustes em STATE.md**: violaria padrão de `memory-debrief` (propõe → mostra → aplica após sinal verde).
- **Estender `memory-bootstrap`**: mistura escopos (carregar contexto vs reconciliar pós-pull); skill separada é mais legível e invocável manual.
