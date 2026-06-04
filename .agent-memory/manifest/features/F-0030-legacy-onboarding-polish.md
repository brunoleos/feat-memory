---
id: F-0030
name: legacy-onboarding-polish
status: shipped
introduced: 2026-06-04
version: 0.14.0
user_value: >
  Lapidações de consistência e credibilidade na adoção legacy: o audit conecta
  schema 0.00 por frontmatter ausente ao remédio (re-deployar); o .meta.yaml
  para de vazar caminho local; o budget morto feature_file_max_bytes sai e a
  skill instrui leanness; o STATE gerado passa em linter Markdown; o bloco da
  AGENTS.md não duplica as descrições das skills; e os caminhos impressos usam
  separador nativo do SO.
contracts:
  api:
    - src/agent_memory/governance/audit.py::run
    - src/agent_memory/deploy.py::deploy_meta
    - src/agent_memory/deploy.py::print_next_steps
    - src/agent_memory/memory/checkpoints.py::render_state
  data:
    - src/agent_memory/data/templates/STATE.md
    - src/agent_memory/data/templates/AGENTS.md
  tests:
    - tests/test_upgrade_guard.py
    - tests/test_meta.py
acceptance:
  - {id: A1, pattern: event, trigger: "o audit encontra AGENTS.md sem frontmatter (campos ausentes) e o CLI é mais novo que a versão deployada", response: "imprime a remediação dirigida: re-rode `agent-memory deploy` para injetar o esqueleto de frontmatter"}
  - {id: A2, pattern: ubiquitous, requirement: "o .meta.yaml gravado pelo deploy não contém mais `cli_path` (ADR-0034)"}
  - {id: A3, pattern: ubiquitous, requirement: "nenhum template declara `feature_file_max_bytes`; a skill instrui arquivos de feature enxutos sem limite mecânico"}
  - {id: A4, pattern: ubiquitous, requirement: "o STATE.md (template e gerado por render_state) tem um título h1 e tabela com pipes espaçados — passa MD041/MD060"}
  - {id: A5, pattern: ubiquitous, requirement: "o bloco agent-memory da AGENTS.md lista as skills de forma terse (roster), sem duplicar as descrições que vivem no frontmatter de cada SKILL.md"}
  - {id: A6, pattern: ubiquitous, requirement: "print_next_steps usa o separador de path nativo do SO e aponta `agent-memory schema` como referência de campos"}
depends_on: [F-0025, F-0027]
decisions: [ADR-0034]
---

# F-0030 · legacy-onboarding-polish

Feature guarda-chuva para as lapidações de prioridade média/baixa do relatório da
Tensegrams (W4–W9): guard de upgrade ligando o sintoma (schema 0.00) à causa/solução;
remoção do `cli_path` do meta versionado (ADR-0034); remoção do budget morto
`feature_file_max_bytes` com leanness movida para guidance da skill; STATE template e
`render_state` passando em MD041/MD060 (título h1 + tabela espaçada); enxugamento da
duplicação das descrições de skills entre SKILL.md e o bloco da AGENTS.md; e caminhos
impressos com separador nativo do SO, com link para `agent-memory schema`.
