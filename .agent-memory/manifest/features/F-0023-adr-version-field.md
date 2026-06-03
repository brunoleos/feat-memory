---
id: F-0023
name: adr-version-field
status: shipped
introduced: 2026-06-03
version: 0.11.0
user_value: >
  o campo `version` em ADRs deixa de ser drift ambíguo (presente em uns, ausente
  em outros, sem regra) e vira opcional formalizado: validado quando presente,
  pré-preenchido em novos drafts, documentado na METHODOLOGY.
contracts:
  api:
    - src/agent_memory/memory/schemas.py::validate_decision
    - src/agent_memory/memory/schemas.py::SEMVER_RE
    - src/agent_memory/memory/propose_adr.py::generate_draft
  tests:
    - tests/test_adr_version.py
acceptance:
  - {id: A1, pattern: state, state: "ADR tem `version` no formato X.Y.Z", response: "validate_decision não emite Issue por causa do campo"}
  - {id: A2, pattern: unwanted, trigger: "ADR tem `version` malformado (ex: `0.11` ou `v1`)", response: "Issue severity=error"}
  - {id: A3, pattern: ubiquitous, requirement: "ADR sem `version` é válido — o campo nunca é exigido (imutabilidade de ADRs antigos preservada, ADR-0003)"}
  - {id: A4, pattern: event, trigger: "`agent-memory propose-adr` gera draft", response: "frontmatter inclui `version: <versão atual do pacote>`"}
depends_on: []
decisions: [ADR-0027]
---

# F-0023 · adr-version-field

Fecha o drift do campo `version` em ADRs. Opcional por decisão (ADR-0027): sem
backfill, validado só quando presente. `SEMVER_RE` é a fonte única de formato,
reusada pelo template do propose-adr.
