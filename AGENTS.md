---
schema_version: 2
project: agent-memory
stack:
  language: python>=3.11
  packaging: setuptools (src layout, importlib.resources para package data)
  testing: pytest
  distribution: pipx editable install (PyPI planejado)
constraints:
  - id: C1
    severity: hard
    rule: "Pure Python; sem shell scripts. Tools rodam em Linux, macOS e Windows nativamente."
    check:
      type: forbid_paths
      globs: ["**/*.sh", "**/*.bash"]
  - id: C2
    severity: hard
    rule: "Dependência externa única: pyyaml. Novas dependências exigem ADR."
    check:
      type: dependencies
      manifest: pyproject.toml
      allow: ["pyyaml"]
  - id: C3
    severity: hard
    rule: "O projeto segue a metodologia agent-memory para gestão de agentes LLM."
  - id: C4
    severity: hard
    rule: "Toda documentação em pt-br."
references:
  manifest_index: ./.agent-memory/manifest/INDEX.md
  state: ./.agent-memory/STATE.md
  decisions_index: ./.agent-memory/decisions/INDEX.md
  methodology: ./METHODOLOGY.md
  skills: ./skills/
budgets:
  resumption_max_bytes: 12288
  state_max_bytes: 4096
---

# Constituição do projeto

## Identidade

`agent-memory` é uma CLI Python que distribui uma metodologia de memória persistente para agentes LLM (Claude Code, Cursor, Aider e qualquer ferramenta que reconheça `AGENTS.md`). Quatro artefatos versionados (`AGENTS.md` na raiz; `STATE.md`, `manifest/` e `decisions/` em `.agent-memory/`) dão ao agente contexto durável entre sessões; um conjunto de subcomandos (`deploy`, `audit`, `propose-adr`, `migrate`, `archive`, `checkpoint`, `record`/`log`, `version-check`, `check-*-staged`) automatiza instalação, validação, gênese retroativa e governança. Quatro skills (`memory-deploy`, `memory-bootstrap`, `memory-debrief`, `memory-pull-brief`) orientam os fluxos críticos. Usuários: desenvolvedores que querem que seu agente preserve foco e decisões arquiteturais sem reler o código a cada sessão.

Este repositório é simultaneamente a tool e a metodologia — vale o C3: o projeto segue o próprio protocolo.

## Restrições não-negociáveis

As restrições marcadas como `severity: hard` no frontmatter são auditadas pelo `agent-memory audit` e bloqueiam o build quando violadas. As `soft` geram apenas warning. Mudanças nesta lista exigem ADR.

Constraints podem declarar um bloco `check` opcional que o `agent-memory audit` **executa** contra o repositório, tornando a restrição enforced em vez de só declarativa ([ADR-0028](.agent-memory/decisions/0028-constraints-declarative-checkers.md)). C1 (`forbid_paths` sobre `*.sh`/`*.bash`) e C2 (`dependencies` sobre `pyproject.toml`, allow `pyyaml`) são checadas a cada audit; a violação herda a severity da constraint. C3 e C4 ficam declarativas — não há checker barato e confiável para elas.

A combinação `pure Python` + `pyyaml apenas` é o que torna o `pipx install` trivial em qualquer plataforma. Adicionar shell scripts ou outras dependências fragmenta a superfície de instalação e exige ADR.

## Convenções de código

Observado em refactors recentes (não confirmado como regra dura): módulos da CLI tendem a usar **lazy initialization** — `yaml` importado dentro das funções que precisam, `ROOT` e paths derivados computados sob demanda. Veja [src/agent_memory/governance/audit.py](src/agent_memory/governance/audit.py), [src/agent_memory/memory/propose_adr.py](src/agent_memory/memory/propose_adr.py). Mantém startup barato e desacopla import do CWD.

Templates em `src/agent_memory/data/templates/` usam o token literal `{VERSION}`, substituído em runtime pelo `deploy.py` com a versão do pacote. Não escreva versões hardcoded em templates.

Pre-commit hook é fail-open: se o binário `agent-memory` não está no PATH, emite warning e libera o commit. Documentado em [src/agent_memory/governance/data/hooks/pre-commit](src/agent_memory/governance/data/hooks/pre-commit).

Código, identificadores e nomes de arquivos em inglês; documentação em pt-br (C4).

## Desenvolvimento local

Este repositório é a fonte da tool e ao mesmo tempo um projeto consumidor da metodologia (C3). Para instalar/atualizar a CLI a partir do código local, use **pipx editable install** — é o mecanismo de distribuição formalizado em [ADR-0007](.agent-memory/decisions/0007-distribute-as-pipx-package.md):

```bash
python -m pipx install --force -e .
```

`--force` reinstala se já houver versão pipx-instalada (típico). Após esse comando, mudanças em `src/agent_memory/` aparecem imediatamente em `agent-memory <subcomando>` (editable install) — não é preciso reinstalar a cada edição. Bumps de versão em `VERSION` e mudanças em `pyproject.toml` exigem reinstall para refletir em `agent-memory.__version__`.

Não use `pip install -e .` — colide com o shim do pipx em `~/.local/bin/agent-memory.exe` e produz erro de permissão no Windows.

<!-- >>> agent-memory >>> -->
## agent-memory

Sessões começam por `.agent-memory/STATE.md` (foco atual) e `.agent-memory/manifest/INDEX.md` (mapa de capacidades). Detalhes de uma feature ficam em `.agent-memory/manifest/features/F-NNNN-*.md`. Decisões arquiteturais em `.agent-memory/decisions/`. A metodologia completa está documentada no repositório do agent-memory: <https://github.com/brunoleos/agent-memory/blob/v0.14.0/METHODOLOGY.md>.

Este bloco é refrescado a cada `agent-memory deploy`. Não edite diretamente — mudanças aqui são sobrescritas no próximo redeploy. Conteúdo específico do projeto vai fora das marcações HTML que delimitam este bloco.

### Skills disponíveis

Quatro skills em `skills/` orientam os fluxos críticos. Leia o `SKILL.md` de cada uma antes de executá-la — o frontmatter traz os triggers de ativação e as instruções autoritativas (fonte única; não duplicadas aqui). Roster:

- **`memory-deploy`** — instalar/adotar a metodologia num projeto: deploy mecânico e, em legacy, gênese retroativa multi-fonte (testes, telas, código, deps; git secundário).
- **`memory-bootstrap`** — retomar uma sessão: carregar o contexto e dar o briefing tático ("onde paramos", "qual o status").
- **`memory-debrief`** — fechar/commitar uma sessão: atualizar Manifest e STATE e propor ADR a partir do diff. A mais usada no dia-a-dia.
- **`memory-pull-brief`** — após `git pull`, brifar o que veio do remote e ressincronizar o STATE.

### Como retomar trabalho

A constituição é carregada automaticamente. Em seguida, você deve carregar `.agent-memory/STATE.md` para descobrir o foco da sessão e os IDs de features e decisões ativas. Apenas as features e ADRs listados em `STATE.md::active_features` e `STATE.md::active_decisions` precisam ser expandidos no contexto inicial — carregar o Manifest inteiro ou todos os ADRs viola o orçamento de retomada.
<!-- <<< agent-memory <<< -->
