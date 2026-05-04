---
id: ADR-0013
date: 2026-05-03
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0010, F-0011, F-0014]
related: [ADR-0007, ADR-0011]
tags: [deploy, meta, version, observability]
---

# ADR-0013 · Deploy grava `.agent-memory/.meta.yaml` com versão e timestamp

## Contexto

A versão do `agent-memory` que produziu a estrutura de um projeto consumidor hoje só vive implícita nas URLs `blob/v{VERSION}/METHODOLOGY.md` que o template de `AGENT.md` interpola via [`_copy_template`](src/agent_memory/deploy.py) (substituição literal de `{VERSION}` pelo valor de `__version__` em [src/agent_memory/__init__.py](src/agent_memory/__init__.py)). Isso significa que descobrir a versão exige parsing frágil de markdown — quebra se o usuário editar a URL, e nenhum subcomando da CLI consegue reportar "auditado contra v0.6.0" sem re-executar o parsing.

Três usos imediatos pediam a versão como dado de primeira classe:

1. **Audit cross-check** (F-0011): emitir relatórios e exit codes contra a versão usada no último deploy, para flagrar quando a estrutura ficou desincronizada da CLI instalada.
2. **Telemetria de aderência** (F-0014): cada evento (`session_start`, `debrief_run`) precisa carregar a versão para comparar adesão entre upgrades.
3. **Suporte ao usuário**: "qual versão você está rodando?" hoje não tem resposta sem inspeção manual de filesystem.

ADR-0007 já formalizou o `pipx install` como mecanismo de distribuição, e a versão fica gravada na metadata do package. Mas o contrato é entre CLI e PyPI — o consumidor não tem visibilidade.

## Decisão

O `agent-memory deploy` grava `.agent-memory/.meta.yaml` no consumidor após copiar templates, com o seguinte schema mínimo:

```yaml
schema_version: 1
version: 0.6.0
deployed_at: 2026-05-03T19:42:11+00:00
cli_path: /home/user/.local/bin/agent-memory
telemetry_enabled: true
```

Campos:

- `schema_version` (int, obrigatório): versão do schema do próprio `.meta.yaml`. Permite evolução futura sem quebrar leitores antigos.
- `version` (str, obrigatório): valor de `agent_memory.__version__` no momento do deploy.
- `deployed_at` (str ISO 8601 UTC, obrigatório): timestamp do deploy mais recente. Sobrescrito a cada `agent-memory deploy`.
- `cli_path` (str, obrigatório): caminho absoluto do executável `agent-memory` que rodou o deploy. Útil para diagnóstico ("estou usando a CLI certa?").
- `telemetry_enabled` (bool, opcional, default `true`): kill switch para F-0014. Default ligado por escolha em ADR-0017.

A CLI ganha flag `--version` no parser raiz, exibindo `__version__` e saindo com 0. Comportamento idêntico ao padrão `argparse`.

A `audit.py` ganha helper `read_meta(root: Path) -> dict | None` que lê `.agent-memory/.meta.yaml` se existe, retorna `None` se ausente. Tolerância a ausência é deliberada: consumidores instalados antes desta versão não têm o arquivo, e features que o consultam (F-0011, F-0014) devem degradar graciosamente.

O arquivo `.meta.yaml` **é versionado no Git** do consumidor. Não é volátil como STATE.md — é metadata de instalação, paralelo a `package.json` ou `pyproject.toml`. A única exceção é `cli_path`, que pode variar por máquina e contribuidor; aceitamos esse churn como custo de ter rastreabilidade local.

## Consequências

**Positivas**:

- Versão deixa de ser implícita. F-0011 pode ler `.meta.yaml` antes de qualquer validação cross-version. F-0014 pode anotar todo evento de telemetria com a versão.
- `agent-memory --version` funciona como qualquer CLI moderna espera, eliminando uma fricção de UX trivial mas constante.
- Suporte assíncrono fica viável: usuário cola `cat .agent-memory/.meta.yaml` num issue e o mantenedor sabe imediatamente o ambiente.
- Schema independente do schema dos artefatos da metodologia (`schema_version: 2` vive em STATE.md/manifest/ADR). Mudanças no `.meta.yaml` não exigem migração dos artefatos.
- Tolerância a ausência é simétrica com o padrão do projeto: helpers retornam `None` ou `{}`, callers decidem a política. Coerente com `parse_frontmatter` em [audit.py:129](src/agent_memory/audit.py#L129).

**Negativas**:

- Mais um arquivo no consumidor para manter coerente. O risco é o usuário editar manualmente e introduzir drift; mitigado documentando "regenerado por `agent-memory deploy`" no header do template.
- `cli_path` gera ruído em commits multiusuário (paths absolutos diferem por máquina). Aceito porque o valor diagnóstico vence em projetos solo, e em times pode ser pacificado por regra de `.gitattributes` se desejado.
- Acopla F-0011/F-0014 a um arquivo extra. Quem rodou `deploy` antes desta versão não vê os benefícios até re-deployar. Aceito como custo único de upgrade.

## Alternativas rejeitadas

**Embutir a versão num campo do frontmatter de AGENT.md** (ex: `installed_version: 0.6.0`). Funciona mas mistura metadata de instalação com configuração editável pelo usuário. AGENT.md já tem campos do projeto (`project`, `constraints`); adicionar metadata de tooling polui a separação de responsabilidades. Rejeitada por acoplamento ruim.

**Usar `pyproject.toml` da CLI via `importlib.metadata` no consumidor**. Não funciona — o consumidor não tem dependência declarada no `agent-memory`; a CLI vive no ambiente Python dele, não no projeto. Rejeitada por inviabilidade.

**Gravar só em arquivo ignorado pelo Git** (ex: `.agent-memory/.cache/version`). Reduziria churn de `cli_path` mas perderia rastreabilidade histórica ("desde quando estamos em v0.6.x?"). Rejeitada por jogar fora o sinal mais valioso.

**JSON em vez de YAML**. Mais simples para parser, mas o resto do projeto usa YAML em frontmatter; consistência vence pela penalidade leve de adicionar `yaml.safe_dump` em mais um lugar (já é dependência obrigatória). Rejeitada por inconsistência.
