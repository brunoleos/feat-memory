---
id: ADR-0049
date: 2026-06-30
status: accepted
version: 2.3.2
supersedes: null
superseded_by: null
affects_features: []
related: [ADR-0043, ADR-0016]
tags: [process, refactor, testing, methodology]
---

# ADR-0049 · Renomeações/remoções exigem varredura exaustiva + guard de símbolos removidos

## Contexto

A remoção do `STATE.md` (cutover 2.0.0) e os renames subsequentes (`suggestions`→`ideas`, `planned`→`proposed`, `migrate --to=changelog` removido) deixaram **referências mortas espalhadas**: gates de commit, seeding do migrate, patcher de frontmatter, `schema_reference`, `telemetry`, `archive` (bug **funcional**), docstrings, skills. Várias só foram pegas pelo **dogfood do cliente, em produção** — em três rodadas seguidas. A causa-raiz não foi falta de atenção: foi enumerar as referências de um símbolo removido **por raciocínio** (lossy, humano) em vez de **por busca exaustiva** (completa, mecânica).

## Decisão

Toda renomeação/remoção de artefato ou comando segue um ritual mecânico:

1. **Varredura exaustiva no início.** `grep -rn` de **todas** as formas do símbolo em todo o repo (src, tests, skills, templates, hooks, docs) → checklist; cada hit classificado como *migrar* ou *intencional-histórico*.
2. **Verificação no fim.** Re-grep até **zero** referências ativas (só restam as intencionais).
3. **Guard automatizado.** `tests/test_no_stale_cutover_refs.py` falha se uma superfície **shipada** (skills/templates/data) citar comando/arquivo removido — pega a regressão antes de shipar, sem depender do dogfood do cliente.

## Alternativas rejeitadas

- **"Prestar mais atenção":** não-confiável — o erro é de método, não de esforço.
- **Guard que proíbe qualquer menção a `STATE.md`:** falso-positivo nas menções intencionais (retrocompat no audit; explicação nas skills). O guard mira só comandos/arquivos **removidos**, que não têm uso legítimo vivo.
