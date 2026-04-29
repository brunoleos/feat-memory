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

# ADR-0001 · Adotar AGENT.md como constituição multi-agente, com CLAUDE.md como redirect

## Contexto

Diferentes ferramentas LLM esperam arquivos de instruções diferentes (`CLAUDE.md` para o Claude Code, `.cursorrules` para o Cursor, `.aider.conf` para o Aider, etc.). Distribuir uma metodologia que precise ser duplicada por ferramenta gera drift rápido — uma mudança em uma não propaga para as outras, e a constituição perde valor como fonte única de verdade.

A convenção `AGENT.md` emergiu como ponto de convergência cross-tool, com adoção crescente em ferramentas que reconhecem o nome diretamente.

## Decisão

`AGENT.md` é o arquivo canônico da constituição do projeto. Para o Claude Code, mantemos um `CLAUDE.md` mínimo na raiz contendo apenas `@AGENT.md` (sintaxe de import do Claude Code), que faz a ferramenta carregar a constituição via redirect.

Times usando uma única ferramenta podem manter apenas o arquivo correspondente; times multi-agente compartilham a mesma constituição sem duplicação. Suporte a uma ferramenta nova exige só criar o shim apropriado análogo ao `CLAUDE.md`.

## Consequências

Zero duplicação de instruções por ferramenta — a constituição vira fonte única de verdade auditável e versionada. Adicionar suporte a uma ferramenta nova é trivial. `CLAUDE.md` vira "redirect" exceto quando o usuário precisa adicionar instruções específicas do Claude Code que não fazem sentido em outros agentes (caso documentado na skill `memory-deploy`).

Custo: dependência da convenção AGENT.md ser estável e amplamente adotada. Se a convenção fragmentar no ecossistema, a estratégia de redirect precisa ser revisada.

## Alternativas rejeitadas

Manter um arquivo por ferramenta (`CLAUDE.md` + `.cursorrules` + `AGENT.md`) foi rejeitado porque garante drift — mudança em um não propaga para os outros, e a sincronização manual é incompatível com o volume de mudanças esperado.

Usar só `CLAUDE.md` como canônico foi rejeitado porque amarra o nome a uma ferramenta específica e fica cada vez mais errado conforme outras ferramentas adotam `AGENT.md`. Posicionamento do projeto sofre.

Gerar arquivos por ferramenta a partir de uma fonte única foi rejeitado por adicionar complexidade de build (gerador, hook de regeneração, validação de output) sem ganho real para times que usam só uma ferramenta — que é a maioria dos casos.
