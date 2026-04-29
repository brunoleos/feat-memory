---
id: ADR-0006
date: 2026-04-29
version: v0.2.0
status: superseded
supersedes: ADR-0005
superseded_by: ADR-0007
affects_features: [F-0001]
related: []
tags: [installation, distribution]
---

# ADR-0006 · Gitignore `.agent-memory/` e re-clone em fresh checkouts

## Contexto

O modelo da v0.1.0 (ADR-0005) versionava `.agent-memory/` no projeto consumidor. Conforme a tool foi adotada em mais projetos, dois custos ficaram inaceitáveis. Primeiro, cada `git pull` na tool produzia um diff gigante no histórico do projeto consumidor, poluindo o `git log` com mudanças que não pertencem ao projeto. Segundo, a duplicação fazia com que cada projeto carregasse seu próprio fork congelado da tool, dificultando upgrade coordenado entre múltiplos projetos.

Era preciso uma estratégia que mantivesse a simplicidade do modelo "tool dentro do projeto" mas eliminasse a poluição do histórico Git.

## Decisão

O `.agent-memory/` continua sendo clonado dentro do projeto, mas passa a ser **gitignored**. O `deploy.py` da v0.2.0 adiciona automaticamente a entrada ao `.gitignore` do projeto consumidor via bloco com sentinelas (idempotente). O fluxo de update vira três comandos: `rm -rf .agent-memory && git clone --branch <tag> ... .agent-memory && python .agent-memory/deploy.py`. Em fresh checkouts, o usuário re-clona a tool antes de rodar deploy.

Como efeito colateral coerente da mesma decisão, skills passaram a ser sempre atualizadas pelo deploy (em vez de puladas se já existiam) — são conteúdo de metodologia, não de usuário, e a expectativa explícita é que reflitam sempre a versão corrente da tool.

## Consequências

Histórico Git do projeto consumidor fica limpo — mudanças no projeto e mudanças na tool ficam separadas. Cada projeto pode pinar a versão da tool independentemente via tag no clone, sem que isso apareça no histórico do projeto. O bloco com sentinelas em `.gitignore` permite refresh idempotente sem destruir entradas que o usuário adicionou fora do bloco.

Custo principal: fresh checkouts não são mais autocontidos — o usuário precisa re-clonar a tool antes de rodar deploy. O `.agent-memory/` no disco fica fora do controle de versão do projeto, exigindo disciplina para manter a versão certa em uso. A operação `rm -rf` no fluxo de update é frágil e propensa a deixar versões inconsistentes entre projetos.

## Alternativas rejeitadas

Manter o modelo da v0.1.0 (versionado) foi rejeitado pelo custo já documentado de poluição do histórico e duplicação.

Instalar via pip foi novamente considerado mas adiado: a tool ainda não tinha entry point CLI nem layout de packaging adequado, e a mudança seria muito grande para um único incremento. A decisão foi tomar o passo intermediário (gitignore) que elimina o problema mais agudo, e tratar a transição para package manager como decisão posterior.
