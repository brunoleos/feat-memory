---
id: ADR-0004
date: 2026-04-28
version: v0.1.0
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0006, F-0007, F-0008]
related: []
tags: [skills, ux, methodology]
---

# ADR-0004 · Skills separadas por momento (deploy, bootstrap, debrief)

## Contexto

A metodologia tem três momentos qualitativamente diferentes (instalar, iniciar sessão, fechar unidade de trabalho), cada um com checklist própria e riscos de execução errada distintos. Uma skill monolítica que cobre tudo tem trigger genérico e o agente erra a fase.

## Decisão

Três skills independentes (`memory-deploy`, `memory-bootstrap`, `memory-debrief`), cada uma com `description` declarando triggers de ativação e instruções autoritativas no corpo. Skills curtas tendem a ser invocadas no momento certo; monolíticas tendem a ser ignoradas. Conteúdo de "porquê" vive em METHODOLOGY (fonte canônica); skills só cobrem "como executar" — reduz risco de drift entre elas.

(Uma quarta skill `memory-pull-brief` foi adicionada em ADR-0012, mantendo o mesmo princípio.)

## Alternativas rejeitadas

- **Skill monolítica `memory-methodology`**: trigger ambíguo; agente erra a fase (executa debrief no início, bootstrap quando o usuário pediu install).
- **Nenhuma skill, só METHODOLOGY**: agentes reconstroem o protocolo a cada interação, executam inconsistentemente.
