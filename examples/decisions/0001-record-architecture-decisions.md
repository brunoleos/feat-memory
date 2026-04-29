---
id: ADR-0001
date: 2026-04-22
status: accepted
supersedes: null
superseded_by: null
affects_features: []
related: []
tags: [meta, methodology]
---

# ADR-0001 · Adotar registros de decisão arquitetural

## Contexto

Decisões arquiteturais — escolhas de stack, padrões, trade-offs — são tomadas continuamente no projeto. Sem registro estruturado, o contexto das escolhas se perde, novos contribuidores (humanos ou agentes LLM) repetem discussões já encerradas, e fica impossível distinguir intenção deliberada de acidente histórico.

O custo de não registrar não aparece imediatamente. Ele se manifesta seis meses depois, quando alguém pergunta "por que escolhemos X?" e a resposta é "ninguém lembra exatamente". Quando isso acontece, a equipe geralmente reabre a discussão e refaz o trabalho de avaliação, desperdiçando tempo que já foi gasto uma vez.

## Decisão

Adotar Architecture Decision Records (ADRs) como forma única de registrar decisões arquiteturais não-triviais. Cada ADR é um arquivo markdown imutável em `decisions/NNNN-slug.md`, com frontmatter YAML estruturado e seções padronizadas: Contexto, Decisão, Consequências, Alternativas rejeitadas.

ADRs nunca são editados após `status: accepted`. Mudanças de direção exigem um novo ADR com `supersedes: ADR-XXXX`, e o ADR original tem apenas seu campo `superseded_by` atualizado — o conteúdo original é preservado.

A regra prática para decidir se uma escolha merece ADR: se um futuro contribuidor olhando o commit em seis meses precisaria de explicação para entender a escolha, vire ADR. Se a explicação cabe no commit message, não vale o esforço.

## Consequências

Decisões ficam auditáveis com proveniência completa. Novos agentes leem o índice e expandem apenas os ADRs relevantes ao trabalho atual, mantendo o contexto enxuto. O padrão é consolidado desde 2011 (Michael Nygard), com ferramentas existentes (adr-tools, log4brains) caso o time queira automação adicional.

O custo é o esforço marginal de escrever um ADR a cada decisão não-trivial, e a disciplina necessária para não pular o passo. O sistema de auditoria mitiga parcialmente este risco rastreando idade média de decisões e razão de substituição.

## Alternativas rejeitadas

Wiki ou Confluence foi rejeitado porque edição livre destrói história e a documentação não fica versionada com o código. Comentários no código não capturam alternativas rejeitadas e ficam dispersos. Apenas mensagens de commit são curtas demais e desestruturadas, dificultando descoberta retrospectiva.
