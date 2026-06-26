---
schema_version: 2
project: TODO-nome-do-projeto
stack:
  language: TODO
constraints: []
references:
  manifest_index: ./.feat-memory/manifest/INDEX.md
  unreleased: ./.feat-memory/changelog/UNRELEASED.md
  decisions_index: ./.feat-memory/decisions/INDEX.md
  methodology: https://github.com/brunoleos/feat-memory/blob/v{VERSION}/METHODOLOGY.md
  skills: ./skills/
budgets:
  resumption_max_bytes: 12288
---

<!-- feat-memory injetou este frontmatter porque a AGENTS.md existente não tinha
nenhum. `references` e `budgets` já vêm corretos (são mecânicos). Os campos
`project`, `stack` e `constraints` estão como placeholder: o agente os PROPÕE a
partir de evidência do projeto (nome do repo, manifestos, tooling/CI, deps,
lições já escritas em prosa) e apresenta para a SUA aprovação — você revisa,
edita e aprova; nada é cristalizado sem seu aval. Rode `feat-memory schema`
para a forma exata de cada campo (constraints aceitam um bloco `check`
executável, ADR-0028). A prosa de identidade/convenções fora do frontmatter é
autoria sua. Apague este comentário quando terminar. -->
