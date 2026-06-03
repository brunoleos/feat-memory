---
id: F-0021
name: pypi-distribution
status: shipped
introduced: 2026-06-03
version: 0.11.0
user_value: >
  usuário final instala com `pipx install agent-memory` (sem clonar) e cada tag
  vX.Y.Z publica na PyPI automaticamente. Corrige bug de package-data que omitia
  o pre-commit hook do wheel.
contracts:
  api:
    - pyproject.toml
    - .github/workflows/release.yml
  tests:
    - tests/test_packaging.py
acceptance:
  - {id: A1, pattern: ubiquitous, requirement: "package-data declara hooks sob `agent_memory.governance` e templates/skills sob `agent_memory`; todo arquivo de runtime de deploy._data_path é coberto por algum glob"}
  - {id: A2, pattern: event, trigger: "tag `vX.Y.Z` é pushed", response: "release.yml builda sdist+wheel e publica na PyPI via trusted publishing (OIDC, sem token persistente)"}
  - {id: A3, pattern: unwanted, trigger: "um glob de package-data não casa nenhum arquivo, ou um arquivo de runtime fica fora dos globs", response: "test_packaging falha (anti-regressão do bug do split F-0017)"}
  - {id: A4, pattern: ubiquitous, requirement: "metadados PEP 639: license SPDX `MIT` + license-files, sem classifier `License ::` (combinação rejeitada por setuptools recente)"}
depends_on: []
decisions: [ADR-0025]
---

# F-0021 · pypi-distribution

Complementa ADR-0007 (pipx editable para desenvolvimento) com o caminho de consumo
(PyPI). O wheel foi verificado por build real: inclui `governance/data/hooks/pre-commit`,
templates e skills. Publish exige o mantenedor reservar o nome e configurar o trusted
publisher na PyPI — o workflow fica inerte e benigno até lá.
