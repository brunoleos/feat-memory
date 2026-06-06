---
id: F-0027
name: schema-reference
status: shipped
introduced: 2026-06-04
version: 0.14.0
user_value: >
  O agente descobre o schema dos artefatos (campos obrigatórios/opcionais,
  patterns EARS, enums de status, regexes de nome, budgets) sem ler o
  código-fonte do feat-memory: `feat-memory schema` imprime uma referência de
  uma página gerada da própria `schemas.py`, disponível em qualquer projeto
  consumidor. Um doc commitado espelha a mesma saída para leitura humana.
contracts:
  api:
    - src/feat_memory/memory/schema_reference.py::render_schema_reference
    - src/feat_memory/memory/schema_reference.py::add_subparser
    - src/feat_memory/memory/schemas.py::AGENT_REQUIRED
    - src/feat_memory/memory/schemas.py::FEATURE_REQUIRED
  data:
    - docs/SCHEMA-REFERENCE.md
  tests:
    - tests/test_schema_reference.py
acceptance:
  - {id: A1, pattern: event, trigger: "o usuário roda `feat-memory schema`", response: "imprime a referência de schema gerada das constantes de schemas.py"}
  - {id: A2, pattern: ubiquitous, requirement: "a referência cobre, por artefato, os campos obrigatórios e opcionais reconhecidos, os 6 patterns EARS com seus campos, os enums de status, os regexes de nome de arquivo e os budgets (enforced vs advisory)"}
  - {id: A3, pattern: state, state: "as constantes de schemas.py divergem do doc commitado docs/SCHEMA-REFERENCE.md", response: "o teste de sincronia falha, exigindo regenerar o doc"}
  - {id: A4, pattern: ubiquitous, requirement: "as listas de campos obrigatórios são constantes de módulo em schemas.py, consumidas tanto pelos validate_* quanto pelo gerador (fonte única, sem drift)"}
depends_on: []
decisions: []
---

# F-0027 · schema-reference

Fecha a fricção nº1 do relatório da Tensegrams: o schema só era descobrível lendo
`schemas.py` na mesma máquina. As listas de campos obrigatórios foram hoistadas para
constantes de módulo (`AGENT_REQUIRED`, `STATE_REQUIRED`, `FEATURE_REQUIRED`,
`DECISION_REQUIRED`) mais constantes documentais de opcionais; o módulo
`schema_reference.py` renderiza tudo num Markdown via `render_schema_reference`, exposto
por `feat-memory schema` (sempre coerente com o CLI instalado) e materializado em
`docs/SCHEMA-REFERENCE.md` (mantido em sincronia por teste). A skill `memory-deploy` e o
`print_next_steps` apontam o comando como referência.
