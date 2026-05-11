---
id: ADR-0001
date: 2026-04-28
version: v0.1.0
status: accepted
supersedes: null
superseded_by: null
affects_features: []
related: []
tags: [meta, multi-agent, conventions]
---

# ADR-0001 · AGENTS.md como constituição multi-agente; CLAUDE.md como redirect

## Contexto

Diferentes ferramentas LLM esperam arquivos diferentes (`CLAUDE.md`, `.cursorrules`, `.aider.conf`). Duplicar a constituição por ferramenta gera drift rápido.

## Decisão

`AGENTS.md` é o arquivo canônico. Para o Claude Code, mantemos um `CLAUDE.md` mínimo na raiz com apenas `@AGENTS.md` (sintaxe de import do Claude Code) que faz a ferramenta carregar via redirect. Times multi-agente compartilham a mesma constituição sem duplicação; suporte a uma ferramenta nova exige só criar um shim análogo. Custo: dependência da convenção AGENTS.md permanecer estável no ecossistema.

## Alternativas rejeitadas

- **Um arquivo por ferramenta**: garante drift por sincronização manual.
- **`CLAUDE.md` canônico**: amarra a uma ferramenta, posicionamento sofre conforme outras adotam AGENTS.md.
- **Gerar arquivos a partir de fonte única**: complexidade de build sem ganho para times mono-ferramenta (maioria).
