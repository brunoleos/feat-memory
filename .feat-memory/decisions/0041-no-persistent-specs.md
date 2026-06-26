---
id: ADR-0041
date: 2026-06-25
status: accepted
version: 1.5.0
supersedes: null
superseded_by: null
affects_features: []
related: [ADR-0018]
tags: [decisions, manifest, state, methodology, planning]
---

# ADR-0041 · Planejamento é efêmero; o registro durável é ADR + Feature (sem specs)

## Contexto

Durante um redesenho, tentou-se persistir um design doc longo (*spec*). Um spec persistente é um **quinto artefato** que compete com os quatro existentes: duplica o "o quê" (Manifest/Feature) e o "porquê" (decisions/ADR), e apodrece como qualquer artefato que ninguém relê — foi exatamente assim que os checkpoints (ADR-0018) morreram. O risco que um spec parece mitigar — perder o fio do plano num reset de contexto antes de existir artefato durável — tem solução melhor dentro do próprio modelo.

## Decisão

O planejamento de uma sessão é **efêmero**: vive na conversa ou no plan mode da ferramenta, e **não** vira arquivo persistente (nada de `docs/specs/` ou design docs longos). O registro durável de uma sessão é **ADR** (a decisão/porquê) + **Feature** no Manifest (a capacidade/o quê). A disciplina que torna isso seguro: escrever os ADRs **cedo** — mesmo como `proposed` — e os stubs de Feature como `planned` no início do trabalho, para que a retomada dependa de ADR+Feature (que o agente já carrega via `STATE::active_*`) e nunca de um plano efêmero. O artefato de foco operacional + ADR + Feature cobrem o ciclo inteiro; um spec seria a quarta roda.

## Alternativas rejeitadas

- **Specs/design docs persistentes (estilo SDD):** quarto artefato que duplica Manifest+decisions e apodrece; contradiz o princípio de separar por ciclo de mutação — um spec não responde nenhuma pergunta que os outros já não respondam.
- **Plano só na conversa, sem ADR/Feature cedo:** frágil a reset de contexto antes de qualquer artefato durável existir — é o buraco que a disciplina "escreva cedo" fecha.
- **Backfillar um spec ao fim da sessão:** é o checkpoint de novo — narrativa persistida que ninguém relê.
