---
id: ADR-0011
date: 2026-04-30
status: proposed
supersedes: ADR-0010
superseded_by: null
affects_features: [F-0001, F-0006]
related: [ADR-0010]
tags: [deploy, sentinels, scope, skill]
---

# ADR-0011 · Deploy gerencia metodologia em AGENTS.md via bloco com sentinelas

## Contexto

ADR-0010 separava seções por heading com regras distintas — funcionava, mas tinha três frições: a skill ainda autorava conteúdo de projeto na Etapa 4; a taxonomia metodologia/projeto vivia em prosa no SKILL.md (três pontos de mudança coordenados); e o merge envolvia handoff intermediário via `merge-queue` / `pending/AGENT.md.new`. A reflexão apontou para simplificação radical: o deploy não precisa entender semântica de seções — basta a metodologia viver dentro de um bloco delimitado por sentinelas, mesmo padrão de `.gitattributes` e `.gitignore`.

## Decisão

`AGENTS.md` carrega um bloco entre sentinelas HTML (`<!-- >>> agent-memory >>> -->` ... `<!-- <<< agent-memory <<< -->`) contendo intro + `### Skills disponíveis` + `### Como retomar trabalho`. `agent-memory deploy` administra mecanicamente: arquivo ausente → escreve template completo; bloco presente → substitui conteúdo entre sentinelas; bloco ausente → anexa ao final. Tudo fora das sentinelas é preservado byte-a-byte. A função `_replace_sentinel_block` (já usada para `.gitattributes`/`.gitignore`) é parametrizada para aceitar pares customizados. A skill `memory-deploy` perde as etapas 3 (merge) e 4 (personalização de seções) — agora só detecta greenfield/legacy, executa `agent-memory deploy`, e (em legacy) faz gênese retroativa. Mecanismo de merge-queue eliminado; diretório legado removido na primeira execução pós-upgrade. Defesa em profundidade: `partition`/`rpartition` toleram menções literais às sentinelas no conteúdo do bloco.

## Alternativas rejeitadas

- **Manter separação por heading (ADR-0010)**: mantém skill com opinião sobre conteúdo de projeto e handoff via merge-queue. Sentinelas removem ambos com menos código.
- **Arquivo separado importado via `@`**: quebra a convenção de `AGENTS.md` único auto-contido.
- **Não refrescar o bloco em re-deploys**: joga fora a propagação automática de atualizações da metodologia, valor central do editable install.
- **Achar bloco por heading `## agent-memory`**: usuário pode renomear (válido); sentinelas são strings improváveis que documentam o contrato.
- **Drafts com placeholder**: reabre o bug de ADR-0010 (detecção de placeholder vs conteúdo é frágil).
