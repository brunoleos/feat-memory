---
id: ADR-0007
date: 2026-04-29
version: v0.3.0
status: accepted
supersedes: ADR-0006
superseded_by: null
affects_features: [F-0001]
related: []
tags: [installation, distribution, packaging, breaking-change]
---

# ADR-0007 · Distribuir como pacote Python via pipx; CLI no PATH; src layout

## Contexto

O modelo da v0.2.0 (ADR-0006) eliminou a poluição do histórico Git ao gitignorar `.agent-memory/`, mas três problemas residuais ficaram visíveis com o uso continuado.

Primeiro, cada projeto consumidor ainda precisava de um clone separado da tool, multiplicando a manutenção (`git pull` em cada `.agent-memory/`). Segundo, o fluxo de update (`rm -rf` + clone + deploy) era frágil e propenso a deixar versões inconsistentes entre projetos quando o desenvolvedor esquecia de atualizar algum. Terceiro, executar a tool exigia path explícito (`python .agent-memory/deploy.py`), sem ergonomia de CLI.

A maturidade da tool e a estabilização da interface justificavam reabrir a opção de distribuição via package manager Python, que havia sido rejeitada anteriormente por imaturidade da interface.

## Decisão

**BREAKING CHANGE.** Distribuir o `agent-memory` como pacote Python instalável via `pipx`. Layout move para `src/agent_memory/` com src layout padrão. Templates, skills e o pre-commit hook ficam em `src/agent_memory/data/` e são acessados via `importlib.resources` (funciona tanto em editable install quanto em wheel). `pyproject.toml` define o entry point `agent-memory = "agent_memory.cli:main"`, expondo quatro subcomandos (`deploy`, `audit`, `propose-adr`, `migrate`) na CLI. A versão é lida dinamicamente de `VERSION` na raiz.

O caminho recomendado de instalação vira `git clone <tool> ~/dev/agent-memory && pipx install -e ~/dev/agent-memory`. O editable install faz `git pull` no clone refletir imediatamente em todos os projetos consumidores, sem precisar tocar em cada projeto. `agent-memory deploy <projeto>` substitui `python .agent-memory/deploy.py`.

O estado transiente do deploy (merge queue, pending merges) move de `.agent-memory/.merge-queue` para `<projeto>/.agent-memory-deploy/{merge-queue,pending/}` no projeto consumidor (gitignored), separando claramente o lugar onde a tool vive (clone único na máquina) do lugar onde ela opera (cada projeto consumidor).

## Consequências

Um único clone na máquina serve todos os projetos consumidores. CLI no PATH com ergonomia de subcomandos. `git pull` no clone propaga atualizações sem tocar nos projetos. Editable install elimina o passo manual de re-clone que era frágil na v0.2.0. O subcomando `agent-memory audit --init` foi removido (sobreposição funcional com `agent-memory deploy`).

Custo: usuários da v0.1.0/v0.2.0 precisam migrar manualmente — o CHANGELOG documenta os passos. Adoção exige Python e pipx no ambiente do usuário, dependência que antes era opcional. O pacote ainda não está na PyPI (planejado em FUTURE_IMPROVEMENTS), então a instalação atual passa pelo clone editable — `pipx install agent-memory` direto só funcionará após publicação.

## Alternativas rejeitadas

Manter o modelo da v0.2.0 foi rejeitado pelos custos residuais de clone-por-projeto e fluxo de update frágil.

Publicar direto na PyPI sem fase intermediária de editable install foi rejeitado porque queremos validar a interface CLI em uso real antes de comprometer com versionamento estável de pacote publicado. Publicação na PyPI é o próximo passo natural quando a interface congelar.

Manter a tool como scripts standalone (sem `pyproject.toml` nem entry point) e apenas adicionar um wrapper shell foi rejeitado por violar a constraint de pure Python sem shell scripts e por não resolver o problema de instalação one-shot.
