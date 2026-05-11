---
id: ADR-0010
date: 2026-04-30
status: superseded
supersedes: null
superseded_by: ADR-0011
affects_features: [F-0001, F-0006]
related: [ADR-0011]
tags: [deploy, merge, template, skill]
---

# ADR-0010 · Merge de AGENTS.md separa metodologia (sync) de projeto (preservado)

> **Superseded por [ADR-0011](0011-deploy-replaces-agent-md-block-via-sentinels.md):** a separação metodologia/projeto deste ADR ficou implícita e mais simples quando o deploy passou a gerenciar a metodologia inteiramente dentro de um bloco delimitado por sentinelas. Esta proposta original (parser de seções por heading) foi descartada antes de gerar dependências em produção.

## Contexto

O algoritmo de merge da skill `memory-deploy` concatenava o template ao final quando `AGENTS.md` existente tinha conteúdo real mas o template carregava placeholder na mesma seção, produzindo seções duplicadas. Causa raiz: o template misturava mecânica de metodologia (doutrina que deve propagar via re-deploy) com conteúdo de projeto (escrito uma vez, nunca tocado). Qualquer heurística textual falha nas bordas.

## Decisão

Separar seções por categoria com regras de merge distintas. **Metodologia (sync do template)**: intro, `## Skills disponíveis`, `## Como retomar trabalho`. **Projeto (preservadas)**: `## Identidade`, `## Restrições não-negociáveis`, `## Convenções de código`, e qualquer outra `##` adicionada pelo usuário. Template não carrega placeholders para seções de projeto — só comentário HTML marcando ponto de inserção. Ordem fixa do resultado.

## Alternativas rejeitadas

- **Manter placeholders + heurística melhor**: bug original; qualquer detecção de "placeholder vs conteúdo" é frágil.
- **Arquivo separado importado via `@`**: quebra a convenção de que `AGENTS.md` é único e auto-contido, base da portabilidade multi-ferramenta.
- **Marcadores HTML dentro do template** (precursor da abordagem que venceu em ADR-0011): polui o artefato, usuário pode remover. — Esta foi parcialmente reaproveitada em ADR-0011 com sentinelas mais robustas.
