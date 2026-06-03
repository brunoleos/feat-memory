---
schema_version: 2
project: TODO-nome-do-projeto
stack:
  language: TODO
constraints: []
references:
  manifest_index: ./.agent-memory/manifest/INDEX.md
  state: ./.agent-memory/STATE.md
  decisions_index: ./.agent-memory/decisions/INDEX.md
  methodology: https://github.com/brunoleos/agent-memory/blob/v{VERSION}/METHODOLOGY.md
  skills: ./skills/
budgets:
  resumption_max_bytes: 12288
  state_max_bytes: 4096
  feature_file_max_bytes: 6144
---

<!-- agent-memory injetou este frontmatter porque a AGENTS.md existente não tinha
nenhum. Os campos `references` e `budgets` já vêm corretos (são mecânicos). Você
só precisa preencher o que está como TODO/vazio:
  - project: nome do projeto
  - stack: linguagem, arquitetura, deps relevantes
  - constraints: restrições não-negociáveis, cada uma com `id`, `severity`
    (hard|soft) e `rule`; opcionalmente um bloco `check` executável (ADR-0028).
A prosa de identidade/restrições/convenções continua sendo SUA autoria, abaixo
deste bloco. Veja METHODOLOGY.md. Apague este comentário quando terminar. -->
