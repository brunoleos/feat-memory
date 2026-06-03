---
id: ADR-0025
date: 2026-06-03
status: accepted
version: 0.11.0
supersedes: null
superseded_by: null
affects_features: [F-0021]
related: [ADR-0007, ADR-0021]
tags: [distribution, packaging, pypi, ci, release]
---

# ADR-0025 · distribuição via PyPI com trusted publishing

## Contexto

[ADR-0007](0007-distribute-as-pipx-package.md) escolheu `pipx editable install` a
partir do clone como mecanismo de distribuição — ótimo para o desenvolvedor da
própria tool, péssimo para o usuário final, que precisa clonar o repo. O README já
promete `pipx install agent-memory` "quando publicado na PyPI". Falta fechar esse
caminho.

Ao preparar a publicação, descobriu-se um bug latente: o `package-data` de
[pyproject.toml](../../pyproject.toml) declarava `data/hooks/*` sob o pacote
`agent_memory`, mas o split F-0017/ADR-0021 moveu os hooks para
`agent_memory/governance/data/hooks/`. Sem `MANIFEST.in` nem `include_package_data`,
o package-data é a única autoridade para wheels — então **o wheel publicado omitiria
o pre-commit hook**. Editable install mascarava o bug (lê a árvore-fonte direto).

## Decisão

1. **package-data por subpacote.** Cada subpacote declara seu próprio data:
   `agent_memory` (templates, skills) e `agent_memory.governance` (hooks). É
   invariante — `tests/test_packaging.py` valida que todo arquivo de runtime
   (resolvido por `deploy._data_path`) está coberto por algum glob, sem precisar
   buildar um wheel. O bug não pode voltar silenciosamente.

2. **Publicação on-tag via trusted publishing (OIDC).** `.github/workflows/release.yml`
   dispara em tag `vX.Y.Z`, builda sdist+wheel e publica com
   `pypa/gh-action-pypi-publish` usando OIDC — **sem token de longa duração** no
   repo. `permissions: id-token: write` + environment `pypi`. Mais seguro que API
   token: nada para vazar, escopo amarrado ao repo/workflow.

3. **Metadados PEP 639.** `license = "MIT"` (expressão SPDX) + `license-files`;
   **sem** classifier `License ::` (setuptools recente rejeita a combinação).
   Adicionados `keywords` e `classifiers` (Status, OS Independent, Python 3.11/3.12).

O editable install (ADR-0007) continua sendo o caminho de **desenvolvimento** da
tool; PyPI é o caminho de **consumo**. Não há conflito — ADR-0007 não é superseded,
é complementada.

## Alternativas rejeitadas

- **API token em secret do repo:** funciona, mas é segredo de longa duração que
  pode vazar; OIDC elimina a credencial persistente.
- **`include_package_data = true` + MANIFEST.in:** acopla o wheel ao que o Git
  rastreia e é mais opaco que globs explícitos por subpacote. Globs declarados são
  auditáveis pelo teste.
- **Publicar manualmente com `twine`:** não reproduzível, sem trilha; o trabalho de
  release deve ser mecânico e disparado por tag (coerente com SemVer + CHANGELOG).
- **Manter só pipx-from-clone:** mantém a fricção de adoção que o README já
  reconhece como temporária.
