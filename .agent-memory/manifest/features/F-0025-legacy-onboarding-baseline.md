---
id: F-0025
name: legacy-onboarding-baseline
status: shipped
introduced: 2026-06-03
version: 0.13.0
user_value: >
  Adotar a metodologia num projeto que já tem AGENTS.md em prosa (sem
  frontmatter) produz uma baseline que passa a auditoria de cara, em vez de
  receber 5 erros e conformidade 0.00. O deploy injeta um esqueleto de
  frontmatter (campos mecânicos preenchidos; project/stack/constraints como TODO)
  e o STATE.md nasce com a data real do deploy, sem falso-alarme de frescor.
contracts:
  api:
    - src/agent_memory/deploy.py::_ensure_frontmatter
    - src/agent_memory/deploy.py::_substitute_tokens
    - src/agent_memory/deploy.py::deploy_constitution
  data:
    - src/agent_memory/data/templates/AGENTS.frontmatter-skeleton.md
    - src/agent_memory/data/templates/STATE.md
  tests:
    - tests/test_deploy.py
    - tests/test_packaging.py
acceptance:
  - {id: A1, pattern: event, trigger: "deploy roda numa AGENTS.md existente sem frontmatter (não começa com `---`)", response: "prepende o esqueleto de frontmatter com os 5 campos obrigatórios, preservando a prosa do mantenedor abaixo"}
  - {id: A2, pattern: unwanted, trigger: "a AGENTS.md já tem frontmatter", response: "o deploy não injeta um segundo bloco; o topo do arquivo fica intacto"}
  - {id: A3, pattern: state, state: "esqueleto injetado", response: "`validate_agent` não emite mais 'campo ausente' para schema_version/project/constraints/references/budgets"}
  - {id: A4, pattern: event, trigger: "STATE.md é criado pelo deploy", response: "`updated_at` recebe o instante UTC do deploy (token {DEPLOY_DATE}) e `updated_by` é `deploy`, não a data fixa do template"}
  - {id: A5, pattern: ubiquitous, requirement: "a injeção é idempotente: re-deploy não duplica frontmatter nem bloco de metodologia"}
depends_on: []
decisions: [ADR-0029]
---

# F-0025 · legacy-onboarding-baseline

Fecha a assimetria greenfield/legacy do deploy (ADR-0029): projeto legado com
constituição em prosa parava de receber frontmatter e a auditoria pós-deploy
falhava com conformidade 0.00, com o "próximos passos" mandando editar um
frontmatter inexistente. Agora `deploy._ensure_frontmatter` prepende um esqueleto
neutro (distinto do template greenfield, sem constraints de exemplo Python-só) e
`_substitute_tokens` substitui `{DEPLOY_DATE}` no STATE.md, matando o falso-alarme
de frescor que vinha do `updated_at` hardcoded. É estrutura, não autoria de
identidade — a skill `memory-deploy` migra a prosa para o esqueleto com aprovação
humana.
