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

# ADR-0004 · Três skills separadas (memory-deploy, memory-bootstrap, memory-debrief)

## Contexto

A metodologia tem três momentos qualitativamente diferentes em que o agente precisa ser orientado: instalar a metodologia em um projeto novo, retomar trabalho no início de uma sessão, e fechar uma unidade de trabalho antes do commit. Cada momento tem checklist própria, riscos próprios de execução errada, e triggers linguísticos próprios na conversa.

A pergunta de design é como expor essa orientação ao agente: uma skill monolítica que cobre tudo, ou skills separadas por momento.

## Decisão

Três skills independentes — `memory-deploy` (adoção inicial), `memory-bootstrap` (início de sessão) e `memory-debrief` (fim de unidade de trabalho). Cada skill tem `description` no frontmatter explicitando os triggers de ativação, e instruções autoritativas no corpo. As skills ficam em `skills/` na raiz do workspace consumidor (deployadas a partir de `src/agent_memory/data/skills/` no pacote) e são carregadas pelo agente sob demanda quando o trigger é detectado.

## Consequências

Skills curtas e específicas tendem a ser invocadas no momento certo — o agente reconhece o trigger e dispara a skill apropriada. Cada skill cobre apenas seu fluxo, mantendo o conteúdo digerível para revisão e atualização.

Custo: três arquivos para manter sincronizados quando a metodologia evolui. Mitigação: METHODOLOGY é a fonte de verdade canônica e cobre o "porquê"; as skills cobrem apenas o "como executar" de cada fluxo, reduzindo o risco de drift entre elas.

## Alternativas rejeitadas

Uma skill monolítica `memory-methodology` foi rejeitada porque o trigger ficaria genérico demais. O agente teria que decidir internamente qual fase aplicar e geralmente erra — executa debrief no início da sessão, ou bootstrap quando o usuário pediu para instalar do zero. A separação por momento elimina essa decisão.

Nenhuma skill (apenas METHODOLOGY como referência) foi rejeitada porque deixar o agente reconstruir o protocolo a cada interação produz execução inconsistente. Agentes esquecem passos, pulam fases ou inventam variações. As skills funcionam como checklist autoritativa que evita esses desvios.
