---
id: ADR-0015
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0012]
related: [ADR-0002, ADR-0014]
tags: [manifest, archive, retention, retomada, dogfooding]
---

# ADR-0015 · Arquivamento explícito de features shipped via `feat-memory archive`

## Contexto

`gen_manifest_index()` regenerava INDEX varrendo todas as features. Nada movia features para fora quando viravam `shipped` — o INDEX crescia monotonicamente, e `memory-bootstrap` paga o custo. ADR-0014 já fez F-0011 reconhecer `manifest/archive/` como segundo diretório válido. Faltava mecanismo de movimentação. Pergunta: automaticamente (no audit) ou explícito (subcomando dedicado)?

## Decisão

Novo subcomando `feat-memory archive`. **Default dry-run** — lista o que seria arquivado e sai 0; `--apply` move de fato. Inverte convenção habitual deliberadamente: custo de "esqueci o flag" é zero; "movi sem querer" é commit indesejado. **Critério**: `status == "shipped"` E `id ∉ active_features`. Ambas as condições devem se manter. **Movimento via `git mv`** (preserva blame); fallback `shutil.move`. **Regenera ambos os INDEXes** (`manifest/INDEX.md` para ativas, `manifest/archive/INDEX.md` para arquivadas). **ADRs nunca movem** — registro histórico imutável; `superseded_by` já cobre semântica de "não use mais". `run_audit` ganha varredura adicional de `archive/` para schema e drift; cross-check de F-0011 já busca em ambos.

## Alternativas rejeitadas

- **Automático no audit**: viola separação de responsabilidades (audit informativo vs movimento destrutivo); comportamento mágico difícil de raciocinar quando dá errado.
- **Via flag `audit --archive`**: hook chamaria audit e moveria arquivos durante commits — surpresa horrível.
- **Campo `archived: true` no frontmatter (sem mover)**: feature continua em `features/`, INDEX continua gigante, problema não resolvido.
- **Default `--apply` com `--dry-run` opt-in**: convencional, mas movimentação acidental gera commit não-trivial de reverter.
- **Arquivar ADRs também**: quebra links (`superseded_by` aponta para eles); ADRs já são pequenos no INDEX (uma linha cada).
- **Deletar features shipped**: vandalismo contra C3/ADR-0009 (memória persistente).
