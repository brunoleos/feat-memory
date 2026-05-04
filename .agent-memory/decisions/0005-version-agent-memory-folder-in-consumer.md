---
id: ADR-0005
date: 2026-04-28
version: v0.1.0
status: superseded
supersedes: null
superseded_by: ADR-0006
affects_features: []
related: []
tags: [installation, distribution]
---

# ADR-0005 · Versionar `.agent-memory/` no projeto consumidor (design original)

## Contexto

Para que cada projeto consumidor possa rodar `python .agent-memory/deploy.py` e `python .agent-memory/audit.py`, os scripts da tool precisam estar acessíveis dentro do projeto. A pergunta de design é como os scripts chegam lá. Algumas opções: clone da tool dentro do projeto e versionar; clone da tool dentro do projeto e gitignorar; instalar via package manager.

Na fase inicial da metodologia (v0.1.0), a tool ainda estava sendo validada em uso real e não havia maturidade para decidir sobre publicação em PyPI ou outro registry. Era preciso uma estratégia de distribuição que funcionasse imediatamente, sem dependência de infraestrutura externa.

## Decisão

Clonar a tool dentro do projeto consumidor em `.agent-memory/` e versionar o diretório no Git do projeto. O usuário roda `git clone https://github.com/brunoleos/agent-memory.git .agent-memory` uma vez, depois `python .agent-memory/deploy.py` para instalar a metodologia, e commita `.agent-memory/` junto com o restante do projeto.

## Consequências

Setup é trivial — um clone resolve tudo, sem dependência de gerenciador de pacotes ou ambiente Python específico. Cada projeto fica autocontido: clonar o projeto consumidor traz junto a versão exata da tool que estava em uso. Atualização da tool é via `git pull` ou re-clone manual.

Custo principal (que motivaria a substituição): a tool inteira (scripts, templates, skills) duplica em cada projeto consumidor, e cada `git pull` na tool produz um diff gigante em cada projeto que adota a atualização. O histórico Git do projeto consumidor fica poluído com mudanças que pertencem à tool, não ao projeto.

## Alternativas rejeitadas

Instalar via pip foi rejeitado porque exigia decidir sobre publicação na PyPI antes de ter a metodologia validada em uso real, e adicionava dependência de gerenciador Python no fluxo de adoção.

Submodule Git foi rejeitado por adicionar complexidade operacional (submodule update, init em fresh checkouts) sem ganho claro sobre clone simples na fase de validação.
