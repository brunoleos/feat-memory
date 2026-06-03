---
id: ADR-0027
date: 2026-06-03
status: accepted
version: 0.11.0
supersedes: null
superseded_by: null
affects_features: [F-0023]
related: [ADR-0003]
tags: [schema, decisions, methodology, drift]
---

# ADR-0027 · campo `version` em ADRs é opcional e formalizado

## Contexto

Durante a gênese retroativa do próprio agent-memory (v0.3.0), os ADRs ganharam um
campo `version` no frontmatter — a release em que a decisão foi aceita. A ideia
nunca foi documentada nem validada, e os ADRs recentes (ADR-0023, ADR-0024) já
nasceram **sem** o campo. Resultado: um campo que existe em parte dos ADRs, não em
outros, sem regra — exatamente o tipo de ambiguidade silenciosa que a metodologia
existe para evitar. A sessão anterior, que definiu a semântica de `version` em
features (release de entrega), expôs essa assimetria com decisões.

## Decisão

`version` é um campo **opcional e formalizado** dos ADRs, com semântica simétrica à
das features: a release (`X.Y.Z`) em que a decisão foi aceita / entrou em vigor.

- **Schema** (`validate_decision`): reconhece `version`. Se presente, valida o
  formato `X.Y.Z` (erro se malformado). **Nunca exige** — ADRs sem o campo seguem
  válidos. Implementado com `SEMVER_RE`. O prefixo `v` (`vX.Y.Z`) é aceito por
  compatibilidade: os ADRs da gênese (v0.3.0) usaram essa forma, e são imutáveis
  (ADR-0003) — tolerar é o que evita backfill. Canônico para ADRs novos é `X.Y.Z`,
  alinhado às features.
- **Template** (`propose_adr.generate_draft`): emite `version: <versão atual do
  pacote>` no draft, para que novos ADRs nasçam com o campo preenchido.
- **METHODOLOGY**: documenta o campo na seção de Decisions.
- **Sem backfill.** Não editamos os ~24 ADRs existentes. YAGNI: o valor está em
  novos ADRs nascerem corretos e em o campo ter regra clara, não em uniformidade
  retroativa. ADRs antigos sem `version` não são drift — são válidos por construção.

## Alternativas rejeitadas

- **Tornar `version` obrigatório + backfill de todos os ADRs:** edição em massa de
  registro histórico imutável, alto custo, baixo valor. Quebraria a imutabilidade
  (ADR-0003) por uniformidade cosmética.
- **Remover o campo de vez:** descartaria informação útil (correlacionar decisão ↔
  release) que já existe em ADRs antigos e que o propose-adr pode preencher de graça.
- **Deixar como está (informal):** mantém a ambiguidade — campo presente em uns,
  ausente em outros, sem regra nem validação. É o problema, não a solução.
