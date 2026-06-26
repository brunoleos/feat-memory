---
id: ADR-0047
date: 2026-06-26
status: accepted
version: 2.2.0
supersedes: [ADR-0046]
superseded_by: null
affects_features: [F-0038]
related: [ADR-0040, ADR-0044, ADR-0046]
tags: [future, ideas, lifecycle, methodology]
---

# ADR-0047 · Funil único do futuro (`ideas.md`) + status `proposed` unificado

## Contexto

O feat-memory modelava bem o **passado** (decisions/changelog/manifest-shipped) e o **presente** (UNRELEASED/in_progress), mas o **futuro** era fraco e ambíguo: o `suggestions.md` era um funil mal-escopado (só evolução do sistema de agentes), e a "intenção comprometida" tinha dois nomes para o mesmo estado — feature `planned` vs ADR `proposed`. Um agente pedido a gerar ideias de produto não tinha lar — e não se pode contar com um issue tracker no cliente (o tensegrams não tem).

## Decisão

O futuro vira um pipeline único: **ideia crua (`ideas.md`) → `proposed` (Feature/ADR) → realizando (in_progress / decidindo) → realizado (shipped / accepted)**.

- `suggestions.md` é generalizado e renomeado para **`.feat-memory/ideas.md`**: funil cru para **qualquer** ideia futura (produto **e** meta), tipada. A triagem promove: capacidade→Feature `proposed`; decisão→ADR `proposed`; meta→aplica; senão descarta. Não é tracker de bugs — itens curtos e transitórios (promove ou descarta rápido).
- O status de **entrada é unificado em `proposed`**: feature `planned` passa a `proposed` (o mesmo nome do ADR). As saídas divergem com razão — feature *constrói* → `shipped`; ADR *decide* → `accepted`. A isenção de drift do ADR-0044 carrega para `proposed`.

Supersede parcial do ADR-0046 (regra ADR-0040): o backlog meta-only é substituído por este funil; a retrospectiva inline — parte ainda válida — é re-afirmada no ADR-0048.

## Alternativas rejeitadas

- **Manter `suggestions.md` meta-only + delegar produto ao tracker:** o cliente pode não ter tracker; o futuro fica sem lar.
- **Fundir os ciclos de vida de Feature e ADR:** respondem perguntas diferentes (o quê vs porquê); só a *entrada* (`proposed`) unifica, as saídas divergem.
- **`backlog.md` / `insights.md`:** "backlog" é JIRA-connotado; "insights" conota aprendizado (passado). `ideas.md` é o funil de ação futura mais preciso.
