---
id: ADR-0002
date: 2026-04-28
version: v0.1.0
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0002]
related: []
tags: [schema, audit, constraints]
---

# ADR-0002 · Constraints com severity hard/soft

## Contexto

Restrições de um projeto não são uniformes em peso. Algumas são invariantes que jamais podem ser violadas (ausência de PII em logs, pure Python sem shell scripts, validação obrigatória de schema de borda). Outras são convenções de estilo que podem ser flexibilizadas em casos extremos (docstrings em funções públicas, ordem de imports).

Tratar todas igualmente pelo audit produz dois problemas simétricos. Se tudo é hard, regras razoáveis bloqueiam trabalho legítimo e o time aprende a contornar o audit como rotina. Se tudo é soft, regras críticas perdem peso e violações graves passam despercebidas no ruído de warnings.

## Decisão

Cada entrada em `AGENT.md::constraints` declara `severity: hard | soft` explicitamente no frontmatter. A semântica é direta: `hard` bloqueia o build via `agent-memory audit --strict` (modo usado pelo pre-commit hook e pela CI); `soft` gera apenas warning sem alterar o exit code.

A classificação faz parte do AGENT.md e é responsabilidade do operador do projeto. Mudanças entre níveis (promover soft para hard, ou rebaixar hard para soft) exigem ADR, garantindo que a calibração das regras críticas permaneça uma decisão deliberada.

## Consequências

O audit aplica a mesma engine de validação para os dois níveis, sem ambiguidade sobre qual deveria bloquear. Times comunicam ao agente expectativa explícita sobre o que pode ser flexibilizado em casos extremos versus o que é absolutamente proibido.

Risco principal: inflar a lista classificando tudo como hard "por garantia", recriando o problema que a distinção quis evitar. Mitigação: a exigência de ADR para mudanças desencoraja decisões impulsivas, e o relatório do audit lista a contagem de violações por severity, tornando inflação visível.

## Alternativas rejeitadas

Apenas hard foi rejeitado porque força o usuário a omitir convenções valiosas (que poderiam ser warnings úteis) ou acumular escapes inline no código. O resultado prático é uma constituição empobrecida que captura só o mínimo absoluto.

Apenas soft (todos warnings) foi rejeitado porque enfraquece regras que realmente não podem ser violadas. Em projetos com requisitos de segurança ou compliance, "warning" sobre PII em logs é insuficiente — precisa ser bloqueio.

Severity em três níveis (info / warn / error) foi rejeitada porque o ganho marginal não compensa o custo de calibração. Times perdem mais tempo discutindo se algo é "info" ou "warn" do que ganham com a granularidade extra. Dois níveis cobrem o caso real em 95% dos projetos.
