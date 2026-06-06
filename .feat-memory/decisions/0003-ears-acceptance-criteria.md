---
id: ADR-0003
date: 2026-04-28
version: v0.1.0
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0002]
related: []
tags: [schema, manifest, requirements]
---

# ADR-0003 · Notação EARS para acceptance criteria

## Contexto

Critérios em prosa livre são ambíguos sobre quando o requisito se aplica (sempre? em resposta a gatilho? só em estado X?). Dois leitores divergem, e o agente LLM não tem como validar cobertura.

## Decisão

Critérios seguem EARS com 5 padrões canônicos — `ubiquitous`, `event`, `state`, `optional`, `unwanted` — e `complex` como escape. Cada critério declara `pattern` no frontmatter com os campos obrigatórios (ex: `trigger`+`response` para `event`; `requirement` para `ubiquitous`). `feat-memory audit` valida estrutura — critérios sem `pattern` ou com campos obrigatórios ausentes são erro hard. EARS é convenção estabelecida (origem em Rolls-Royce, NASA, programas de aviônica), curva baixa, sem acoplar a ferramenta de execução.

## Alternativas rejeitadas

- **Prosa livre**: sem validação possível; agente LLM sem ancoragem objetiva.
- **Gherkin (Given/When/Then)**: acopla a BDD (Cucumber, behave); estrutura tripla forçada mesmo onde uma frase basta.
- **User stories**: boas para perspectiva, fracas para verificação automática; complementam, não substituem.
