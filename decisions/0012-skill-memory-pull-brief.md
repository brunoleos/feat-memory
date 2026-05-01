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

# ADR-0012 · Skill `memory-pull-brief` cobre o gap cognitivo pós-pull em projetos cliente

## Contexto

A metodologia tinha três skills cobrindo três momentos: instalar (`memory-deploy`, F-0006), iniciar sessão (`memory-bootstrap`, F-0007) e fechar unidade de trabalho antes do commit (`memory-debrief`, F-0008). Existe um quarto momento crítico não-coberto: **logo depois do `git pull` em projeto cliente que recebeu commits de colegas**.

Os artefatos versionados (`manifest/features/F-*.md`, `decisions/*.md`) chegam já atualizados pelo pull — não há merge mecânico a fazer. Mas há um gap cognitivo: o agente local opera com manifest/decisions diferentes do que viu na sessão anterior, e o usuário humano talvez não saiba o que mudou. Pior, `STATE.md::active_features` e `active_decisions` podem referenciar IDs cuja semântica mudou upstream (uma feature ativa que colega marcou como `shipped`, ou um ADR ativo que foi `superseded`).

Uma proposta anterior (post-merge hook + merge-queue) tentou resolver isso mecanicamente após [ADR-0010](0010-merge-separates-methodology-from-project-sections.md), mas ficou obsoleta com [ADR-0011](0011-deploy-replaces-agent-md-block-via-sentinels.md) — o mecanismo de merge-queue foi eliminado. Nada substituiu o cuidado pós-pull.

## Decisão

Adicionar uma quarta skill — `memory-pull-brief` — espelho de `memory-debrief` em direção contrária: revisa **o que veio do remote** depois do pull, brifa o usuário sobre mudanças semânticas em features/decisions, e propõe ajustes no `STATE.md` local. **Read-only sobre `manifest/` e `decisions/`** — esses já vieram corretos do pull, escrever neles seria reverter trabalho de colegas.

Trigger duplo: manual (frases do usuário) e por delegação a partir de `memory-bootstrap` quando o último commit é merge que tocou artefatos. Sem novo subcomando CLI — toda a lógica é procedural na SKILL.md, usando `git` e `agent-memory audit` direto.

## Consequências

**Positivas**
- Fecha o quarto e último momento crítico do ciclo de vida da memória persistente em projeto cliente (instalar / iniciar / commitar / sincronizar com remote).
- Evita drift silencioso entre `STATE.md::active_*` e a semântica real das features/ADRs após pull.
- Por ser read-only sobre manifest/decisions, não há risco de reverter trabalho de colegas. Aprovação humana antes de tocar STATE.md.
- Custo de manutenção baixo: SKILL.md sem código novo, sem subcomando CLI novo, sem hook git.

**Negativas**
- Aumenta a contagem de skills de três para quatro, levemente expandindo a superfície que o agente precisa conhecer.
- A delegação automática a partir de `memory-bootstrap` adiciona um passo na rotina de início de sessão pós-merge — mitigado por filtragem (encerra em uma frase se nenhum artefato foi tocado).
- Range default `@{1}..HEAD` é heurística que falha se o usuário fez commits locais depois do pull. Mitigado por detecção via `git reflog` e fallback para base explícita.

## Alternativas rejeitadas

**Post-merge git hook automático (proposta anterior, descartada).** Tentava detectar templates atualizados na hora do pull e sinalizar via `merge-queue`. Tornou-se obsoleto com ADR-0011 — não há mais merge-queue, e templates não chegam por `git pull` em projetos cliente (chegam por `pipx upgrade agent-memory`). O hook ficaria sem trigger útil.

**Subcomando CLI `agent-memory pull-brief`.** A lógica é mostly procedural (ler git diff, parsear frontmatter YAML, propor ajustes de STATE) — não há valor mecânico que justifique um binário. Skill-only mantém a superfície da CLI enxuta (quatro subcomandos), enquanto a SKILL.md captura toda a sequência. Pode-se promover para CLI no futuro se a complexidade crescer.

**Auto-aplicar ajustes em STATE.md sem aprovação.** Removeria fricção mas violaria o padrão estabelecido por `memory-debrief` (propõe → mostra → aplica após sinal verde). STATE.md é foco do usuário, não do agente; toques automáticos são intrusivos.

**Estender `memory-bootstrap` em vez de criar skill nova.** Tentado em rascunho — fica longo e mistura dois escopos (carregar contexto vs reconciliar pós-pull). Skill separada é mais legível e permite invocação manual independente do início de sessão.
