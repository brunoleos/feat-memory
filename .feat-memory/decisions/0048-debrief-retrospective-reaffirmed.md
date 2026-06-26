---
id: ADR-0048
date: 2026-06-26
status: accepted
version: 2.2.0
supersedes: [ADR-0046]
superseded_by: null
affects_features: [F-0039]
related: [ADR-0004, ADR-0043, ADR-0046]
tags: [debrief, retrospective, methodology]
---

# ADR-0048 · Retrospectiva inline na debrief (re-afirmada)

## Contexto

O ADR-0046 decidiu duas coisas: a **retrospectiva inline** na debrief e o **backlog de sugestões meta-only**. O ADR-0047 substituiu o backlog por um funil único do futuro (`ideas.md`), superseding o ADR-0046 inteiro para não deixá-lo meio-válido (regra ADR-0040). A retrospectiva continua válida e é re-afirmada aqui como decisão standalone.

## Decisão

Ao fechar a sessão, a `memory-debrief` produz uma **retrospectiva inline** (escopo, bugs, achados, resumo honesto) — e **não persiste a narrativa**. Só as ideias acionáveis vão para o `ideas.md` via triagem (ADR-0047). É o mesmo momento da debrief — não uma 5ª skill (ADR-0004).

## Alternativas rejeitadas

- **Persistir a narrativa por-sessão:** apodrece, como o checkpoint (ADR-0043).
