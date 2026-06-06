---
id: F-0031
name: manifest-capability-guard
status: shipped
introduced: 2026-06-04
version: 0.15.0
user_value: >
  O audit bloqueia features cujo nome é um balde de changelog (polish, misc,
  various, …), forçando o Manifest a permanecer por capacidade nomeável em vez
  de virar um log de release disfarçado.
contracts:
  api:
    - src/feat_memory/memory/schemas.py::validate_feature
    - src/feat_memory/memory/schemas.py::CHANGELOG_NAME_WORDS
  tests:
    - tests/test_changelog_guard.py
acceptance:
  - {id: A1, pattern: event, trigger: "uma feature tem no `name` um token de balde de changelog (ex.: `polish`, `misc`, `various`)", response: "o audit emite um Issue `error`, bloqueando o build, com remediação (divida ou registre no git)"}
  - {id: A2, pattern: ubiquitous, requirement: "o conjunto de tokens (`CHANGELOG_NAME_WORDS`) é fechado e de alta precisão — nenhuma capacidade real trip o guard"}
  - {id: A3, pattern: unwanted, trigger: "tenta-se mecanizar a coesão de conteúdo (vários critérios sem relação)", response: "deliberadamente não é checado — seria ruidoso e mentiria; fica para o litmus humano nas skills (ADR-0035)"}
depends_on: []
decisions: [ADR-0035]
---

# F-0031 · manifest-capability-guard

Backstop mecânico da camada 1 do ADR-0035. `validate_feature` tokeniza o `name` e
bloqueia (`error`) se houver interseção com `CHANGELOG_NAME_WORDS` — o tell de alta
precisão de feature guarda-chuva. Não tenta julgar coesão de conteúdo (ruidoso,
mentiria; fica para o "Teste de uma capacidade" nas skills de autoria). Nasceu da
dissolução do F-0030, que era exatamente esse anti-padrão; o guard teria pego o nome
`legacy-onboarding-polish`.
