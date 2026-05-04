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

# ADR-0003 · Notação EARS para acceptance criteria em features

## Contexto

Critérios de aceitação em features escritos em prosa livre são ambíguos sobre quando o requisito se aplica — sempre? em resposta a um gatilho externo? só enquanto o sistema está em determinado estado? só quando uma feature opcional está ativa? Sem estrutura, dois leitores interpretam o mesmo critério diferentemente, e um agente LLM gerando código a partir do Manifest não tem como validar cobertura.

Frameworks como Gherkin (Given/When/Then) impõem mais cerimônia do que o necessário e misturam-se com BDD/testes, criando acoplamento entre especificação e ferramenta de execução. A indústria de requisitos consolidou a Easy Approach to Requirements Syntax (EARS) precisamente para resolver essa ambiguidade sem amarrar a uma ferramenta específica.

## Decisão

Critérios de aceitação no Manifest seguem a notação EARS com cinco padrões canônicos — `ubiquitous`, `event`, `state`, `optional`, `unwanted` — e `complex` como escape para combinações que não cabem nos cinco. Cada critério declara seu `pattern` no frontmatter e contém os campos obrigatórios para aquele padrão (e.g., `trigger` e `response` para `event`; apenas `requirement` para `ubiquitous` e `complex`).

O `agent-memory audit` valida estrutura: critérios sem `pattern` declarado ou com campos obrigatórios ausentes/vazios são erro de schema e bloqueiam o build em modo strict.

## Consequências

Cada critério deixa explícito o "quando" — sempre, em resposta a X, enquanto em estado Y, opcional, em condição indesejada. Padronização permite ferramentas de tradução para testes, documentação ou contratos de API. EARS é convenção estabelecida na indústria de requisitos (origem em Rolls-Royce, adotada pela NASA e por programas de aviônica), com material didático abundante e baixa curva de aprendizado.

Custos: aprendizado breve dos cinco padrões, e disciplina para não usar `complex` como atalho para escrever prosa livre disfarçada. Mitigação: METHODOLOGY documenta cada padrão com exemplo canônico e instrução explícita de preferir quebrar em múltiplos critérios simples a usar `complex`.

## Alternativas rejeitadas

Prosa livre foi rejeitada porque sem estrutura não há validação possível. Leitores divergem sobre "quando" o requisito vale, e o agente LLM não tem ancoragem objetiva para testar cobertura.

Gherkin (Given/When/Then) foi rejeitado por estar acoplado a BDD e ferramentas de execução (Cucumber, behave). Introduz vocabulário adicional, força estrutura tripla mesmo em casos que pediriam só uma frase, e mistura especificação com mecânica de teste.

User stories ("As a … I want … so that …") foram rejeitadas como substituto porque são boas para descobrir valor e capturar perspectiva do usuário, mas fracas para verificação automática. Geralmente complementam critérios técnicos em vez de substituí-los.
