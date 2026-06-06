---
id: ADR-0023
date: 2026-05-11
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0019]
related: [ADR-0015, ADR-0014]
tags: [decisions, archive, retention, retomada]
---

# ADR-0023 · ADRs superseded vivem em `decisions/superseded/`

## Contexto

ADR-0015 estabeleceu `manifest/archive/` para features shipped e explicitamente rejeitou aplicar o mesmo padrão a ADRs ("ADRs `superseded` ainda são citados; mover quebraria links sem ganho; ADRs já são pequenos no INDEX — uma linha cada"). A simetria com features acabou pesando mais que essa rejeição: o INDEX principal de decisões cresce com cada ADR e nada o desonera; ADRs superseded são registro histórico que continua citável mas não é foco operacional; quem está lendo o INDEX procura o que **vale agora**.

A objeção de ADR-0015 (mover quebra links) só seria verdadeira sem crosscheck consciente do diretório novo — exatamente o que F-0011 (busca de features em `manifest/archive/`) já demonstrou viável. Aplicar a mesma técnica fecha o argumento.

## Decisão

ADRs com `status: superseded` ficam em `.feat-memory/decisions/superseded/`. **Mecânica idêntica a `manifest/archive/`:**

- `gen_superseded_decisions_index` produz `decisions/superseded/INDEX.md` separado do principal.
- `_resolve_active_decision_paths` (audit) busca em `DECISIONS_DIR` E `SUPERSEDED_DIR` — crosscheck nunca falha por causa do move.
- `propose_adr.next_adr_number` agrega IDs de ambos os diretórios + `proposals/` — colisão impossível por construção.
- `check_collisions` continua funcionando sem mudança (ls-tree recursivo de `.feat-memory/decisions` já varre subpastas).

Movimentação atual é **manual via `git mv`** — o subcomando `feat-memory archive` continua reservado a features (ADR-0015 mantida nessa frente). Se a fricção de mover à mão aparecer, evolução natural é `feat-memory archive --decisions` que move ADRs com `status: superseded` E não citadas em `active_decisions`. Sem caso real ainda, YAGNI.

## Alternativas rejeitadas

- **Não separar (manter ADR-0015 íntegra)**: INDEX cresce monotonicamente; superseded enterra accepted como ruído visual.
- **Campo `archived: true` no frontmatter sem mover**: não resolve INDEX (carregado por `memory-bootstrap`); mesma crítica de ADR-0015 às features.
- **Pasta `decisions/archive/` (espelho literal de features)**: "archive" é genérico; "superseded" é o status canônico e bate com o predicado de movimento.
- **Mover ADRs `proposed` que foram descartadas para o mesmo diretório**: confunde semântica (proposed-descartada ≠ superseded por outra). Drafts descartadas continuam em `proposals/` (gitignored ou commit-removed).
- **Automatizar via `feat-memory archive --decisions` já agora**: superfície sem caso real; layout primeiro, automação se justificar.
