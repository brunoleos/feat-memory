---
id: ADR-0021
date: 2026-05-05
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0017]
related: [ADR-0008, ADR-0014, ADR-0016, ADR-0020]
tags: [architecture, separation-of-concerns, refactor, packaging]
---

# ADR-0021 · Separação arquitetural memória × governança em subpacotes

## Contexto

Após a sessão de v0.6.0 (F-0010..F-0016), o pacote `src/agent_memory/` cresceu com 14 módulos misturando dois propósitos diferentes:

- **Memória de agente:** AGENTS.md/STATE.md/manifest/decisions/skills, schemas, parsing, deploy, ciclo de vida (archive, checkpoints, migrate, propose-adr). O agente lê isto.
- **Governança:** audit (drift/freshness/metrics/INDEX gen), hooks, telemetria, check-staleness, check-version-bump, install-hooks. Enforcement disciplinar.

Quando o usuário foi questionado sobre o que o projeto resolve, ele disse: "A parte de memoria do agente é meu foco. Ainda nao sei se preciso da governança." E em seguida: "deixe a separação totalmente independente entre memória de agente x governança."

Sem refactor, nenhum dos dois objetivos pode ser endereçado com clareza. O leitor de `cli.py` vê 9 subcomandos misturados. Quem importa `agent_memory.archive` vai aprender que precisa de `agent_memory.audit` para regenerar índices. Quem quer rodar memória sem governança não tem caminho garantido — o `--no-hooks` em deploy ajuda mas não impede que o consumidor invoque telemetry/check_staleness manualmente.

A pergunta de design não é "separar?", é "**qual a forma da separação**?" — dois pacotes pip distintos, dois CLIs, ou subpacotes internos com mesma CLI?

## Decisão

**Um pacote pip, um CLI, três subpacotes internos com regra de dependência hierárquica:**

```
src/agent_memory/
  __init__.py              # __version__
  cli.py                   # router único, agrupa subcomandos por categoria no --help
  deploy.py                # bootstrap; orquestra memory.* + governance.install_hooks

  shared/                  # utilitários sem opinião sobre o domínio
    paths.py               # ROOT, AGENT, STATE, MANIFEST_DIR, ARCHIVE_DIR, ...
    parsing.py             # parse_frontmatter, read_meta

  memory/                  # artefatos canônicos da metodologia
    schemas.py             # validate_agent, validate_state, validate_feature, validate_decision, EARS
    indexing.py            # gen_manifest_index, gen_archive_index, gen_decisions_index
    archive.py             # move shipped → archive/ (ciclo de vida)
    checkpoints.py         # F-0015 (STATE como view)
    propose_adr.py         # gênese de ADR
    migrate.py             # migração legacy
    data/templates/        # AGENTS.md, CLAUDE.md, STATE.md
    data/skills/           # memory-{bootstrap,debrief,deploy,pull-brief}/SKILL.md

  governance/              # enforcement, telemetria, hooks, métricas
    audit.py               # run_audit (orquestrador) + crosscheck + freshness + collisions + metrics
    telemetry.py           # F-0014
    check_staleness.py     # F-0013
    check_version_bump.py  # F-0016
    version_check.py       # F-0018 (a ser criado)
    install_hooks.py       # instala hooks no consumidor
    data/hooks/pre-commit
```

**Regra de dependência (hierárquica, sem ciclo):**

- `shared/` não importa nada do projeto.
- `memory/` importa apenas de `shared/` e `agent_memory.__version__`.
- `governance/` importa de `shared/` e `memory/` (precisa de `memory.schemas` para validar).
- `cli.py` e `deploy.py` (top-level) importam de tudo (são orquestradores).

**Memory NÃO importa governance.** É a regra que torna `--no-hooks` em deploy uma operação puramente memória. Se um consumidor quiser usar só memória, ele instala normalmente, roda `agent-memory deploy --no-hooks`, e nunca precisa invocar nada de `governance`. Os subcomandos de governança continuam disponíveis mas inertes em relação à memória.

**Decisões pontuais com justificativa:**

- `archive` fica em **memory** (não governance). Move arquivos, não enforça política. É ciclo de vida natural dos artefatos, mesmo padrão de `propose-adr` e `migrate`.
- `audit` fica em **governance** mesmo importando `memory.schemas`. A direção da dependência importa — governance é o orquestrador da validação, não o dono dos schemas. Schemas são fato; audit decide o que fazer com violações.
- `deploy.py` permanece no top-level (não em memory ou governance). É o bootstrap; orquestra ambos os subpacotes. Não pertence a nenhum.
- `cli.py` permanece no top-level com agrupamento de subcomandos por categoria no `--help` via grupos de argparse. O usuário vê duas seções: "Memória" e "Governança".
- **Um CLI, não dois.** UX do consumidor uniforme. Estrutura interna não vaza para a linha de comando. Se no futuro a separação justificar dois pacotes pip ou dois binários, o caminho fica trivial a partir desta estrutura.

## Consequências

**Positivas**:

- Quem quer entender só memória abre `memory/` e ignora `governance/`. Quem quer entender só governança vai direto a `governance/` e usa `memory/` apenas como API estável.
- Drop de governança no futuro vira uma operação cirúrgica (deletar pasta, ajustar `cli.py`, ajustar `deploy.py`, ajustar `pyproject.toml`). Não é decisão acoplada à evolução de memória.
- Schemas centralizados em `memory.schemas` viram contrato público — qualquer ferramenta externa pode importar `from agent_memory.memory import schemas` para validar artefatos sem trazer governança junto.
- A regra `memory ⇏ governance` é verificável mecanicamente (futuro: lint check em CI).
- Adoção de novas features fica clara desde o nascimento: nova validação? Vai em memory.schemas. Novo guard? Vai em governance/.
- O pre-commit hook é shell que invoca CLI, não importa Python — agnóstico ao layout interno. Refactor não toca o contrato com Git.

**Negativas**:

- Refactor toca ~25 arquivos (todos os módulos + todos os testes). Risco de regressão durante o movimento. Mitigação: rodar suíte completa após cada movimento de módulo, manter o comportamento idêntico (zero mudança de contrato externo).
- Imports ficam mais longos: `from agent_memory.governance import audit` vs `from agent_memory import audit`. Aceito como custo da clareza.
- Nome do pacote raiz (`agent_memory`) fica meio-redundante com subpacote (`agent_memory.memory`). Considerado renomear o pacote para `agent_methodology` ou similar, rejeitado por escopo (rename do pacote é breaking change separado).
- Globais lazy-init de paths (`ROOT`, `MANIFEST_DIR`, etc.) que viviam em `audit.py` e eram acessados por outros módulos via `audit.ROOT` agora vivem em `shared.paths` e o acesso é via `shared.paths.ROOT`. Tests existentes que usam `monkeypatch.setattr(audit, "ROOT", ...)` precisam ser atualizados em massa. Mecânico mas tedioso.

## Alternativas rejeitadas

**Dois pacotes pip distintos** (`agent-memory` e `agent-governance`). Mais "totalmente independente" no sentido literal. Rejeitada porque o usuário disse para manter `agent-memory deploy` instalando tudo (resposta #2) — uma única instalação cobre ambos os domínios. Dois pacotes adicionariam custo de release coordenado, dois entry points, dois `pyproject.toml` sem ganho concreto. Caminho permanece aberto se um dia justificar.

**Dois CLIs no mesmo pacote** (`agent-memory` e `agent-governance` apontando para `agent_memory.memory.cli:main` e `agent_memory.governance.cli:main`). Resolveria a clareza no `--help`. Rejeitada porque o consumidor passaria a precisar lembrar dois binários e potencialmente dois conjuntos de subcomandos. Agrupamento por argparse no `--help` único atinge 90% do ganho.

**Manter `audit.py` monolítico, só renomear arquivos para indicar grupo (ex: `governance_audit.py`, `memory_archive.py`).** Cosmético, não resolve a dependência reversa de `archive` chamando `audit.run_audit()`. Rejeitada por falsa solução.

**Refatorar tudo em uma feature, mas com 1 só commit.** Diff impossível de revisar (+1500/-800 estimado). Rejeitada — granularidade da entrega segue a mesma disciplina de F-0010..F-0015 (pequenos commits coerentes).

**Mover deploy.py para `memory/`** porque deploy é principalmente sobre artefatos de memória. Rejeitada porque deploy também instala o hook (governance). Ele orquestra ambos — top-level é o lugar honesto.
