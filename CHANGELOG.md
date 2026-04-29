# Changelog

Todas as mudanças notáveis a esta metodologia são registradas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/) e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.3.0] - 2026-04-29

**BREAKING CHANGE.** Modelo de instalação muda de "clonar para `.agent-memory/`" para "instalar como pacote Python via pipx". A CLI vira `agent-memory <subcomando>` no PATH, eliminando duplicação de scripts em cada projeto consumidor e permitindo que edições no clone reflitam imediatamente em todos os projetos via editable install.

### Adicionado

`pyproject.toml` define o pacote `agent-memory` com entry point `agent-memory = "agent_memory.cli:main"` e package data (`templates/`, `skills/`, `hooks/`) sob `src/agent_memory/data/`. Versão é lida dinamicamente de `VERSION`.

Quatro subcomandos da CLI: `agent-memory deploy <target>`, `agent-memory audit`, `agent-memory propose-adr`, `agent-memory migrate`.

Suite de testes com `pytest` em `tests/`, cobrindo a função de sentinel block, a superfície da CLI, e o fluxo end-to-end de deploy. Dev deps declarados em `pyproject.toml::[project.optional-dependencies] dev`.

Seção "Implicações do editable install" no [USER_GUIDE.md](USER_GUIDE.md) explicando o que muda em `pipx install -e <clone>` vs `pipx install agent-memory` (futuro).

### Mudado

Layout do código move de top-level (`deploy.py`, `tools/`, `templates/`, `skills/`) para `src/agent_memory/` com src layout padrão de packaging Python. Templates, skills e hooks ficam em `src/agent_memory/data/` para serem acessíveis via `importlib.resources`.

`deploy.py` agora aceita o caminho do projeto consumidor como argumento explícito (`agent-memory deploy <target>`), em vez de inferir pela localização do script.

Pre-commit hook agora chama `agent-memory audit --strict --no-index` em vez de procurar `audit.py` em paths fixos. Se o `agent-memory` não está no PATH, emite warning e libera o commit (não bloqueia).

Estado transiente do deploy moveu de `.agent-memory/.merge-queue` e `.agent-memory/.pending-merge/` (dentro do clone-into-project) para `<target>/.agent-memory-deploy/{merge-queue,pending/}` (no projeto consumidor, gitignored).

Skills (`memory-deploy`, `memory-bootstrap`, `memory-debrief`) e documentação atualizadas para usar a nova superfície de CLI.

### Removido

Modelo de "clone para `.agent-memory/`" não é mais suportado. Quem está em v0.1.0/v0.2.0 deve seguir o caminho de migração na seção abaixo.

Subcomando `agent-memory audit --init` (que apenas criava as pastas `manifest/features/` e `decisions/proposals/`) — sobreposição funcional com `agent-memory deploy <projeto>`, que faz o mesmo e mais. Usuários que dependiam de `--init` devem migrar para `agent-memory deploy`.

### Migração de 0.2.0 → 0.3.0

```bash
# 1. Instalar a nova CLI (uma vez na máquina)
git clone https://github.com/brunoleos/agent-memory.git ~/dev/agent-memory
cd ~/dev/agent-memory && git checkout v0.3.0
pipx install -e ~/dev/agent-memory

# 2. Em cada projeto consumidor, rodar deploy (idempotente)
cd /caminho/projeto
agent-memory deploy /caminho/projeto

# 3. Limpar o legado .agent-memory/ (instruções impressas pelo deploy)
git rm -r --cached .agent-memory/
rm -rf .agent-memory
git commit -m "chore: drop .agent-memory/ (agent-memory v0.3.0)"
```

Os artefatos da metodologia (`AGENT.md`, `STATE.md`, `manifest/`, `decisions/`, `skills/`, `.gitattributes`) ficam preservados. Apenas a pasta `.agent-memory/` (que continha a tool clonada) é descartada — a tool agora vive na sua máquina, fora do projeto.

## [0.2.0] - 2026-04-29

Modelo de instalação minimalista: `.agent-memory/` agora é gitignored no projeto consumidor e re-clonado em fresh checkouts, eliminando duplicação no histórico Git. O ciclo de update vira três comandos de shell, sem configuração persistente.

### Mudado

`deploy.py` agora adiciona `.agent-memory/` ao `.gitignore` do projeto consumidor automaticamente (bloco delimitado por sentinelas, idempotente).

`deploy.py` agora sempre atualiza as skills em `skills/` a cada execução (eram puladas se já existiam). Skills são conteúdo de metodologia, não de usuário; quem precisa customizar deve copiar a skill para um nome diferente.

`deploy.py` agora gerencia o `.gitattributes` via bloco com sentinelas, permitindo refresh idempotente do conteúdo da metodologia sem destruir regras locais adicionadas fora do bloco.

### Removido

`update.py`, `.upstream.example`, `.upstream` e `.installed-version`. O fluxo de atualização agora é `rm -rf .agent-memory && git clone --branch <tag> ... .agent-memory && python .agent-memory/deploy.py`.

### Migração de 0.1.0 → 0.2.0

Para projetos que instalaram a v0.1.0 e versionavam `.agent-memory/`, a migração tem quatro passos. O `deploy.py` da v0.2.0 detecta o cenário e imprime as instruções automaticamente quando rodado:

```bash
rm -rf .agent-memory
git clone --depth 1 --branch v0.2.0 \
  https://github.com/brunoleos/agent-memory.git .agent-memory
python .agent-memory/deploy.py
git rm -r --cached .agent-memory/
git commit -m "chore: untrack .agent-memory/ (agent-memory v0.2.0)"
```

Os arquivos da pasta continuam no disco; só saem do índice do Git para que mudanças futuras na tool não apareçam como diff no projeto consumidor.

## [0.1.0] - 2026-04-28

Versão inicial pública. Estabelece a fundação da metodologia.

### Adicionado

Quatro artefatos versionados (`AGENT.md`, `STATE.md`, `manifest/`, `decisions/`) com schemas validados e separação por ciclo de mutação.

Notação EARS completa para critérios de aceitação, com seis padrões (cinco canônicos mais `complex` como escape) validados pelo `audit.py`.

Pre-commit hook que bloqueia commits violando o protocolo, com `--no-verify` como válvula de escape.

Gerador de propostas de ADR (`propose-adr.py`) com detecção de sinais de mudança arquitetural não-trivial e modo `--prompt` para integração com agentes LLM.

Três skills cobrindo os fluxos críticos: `memory-deploy` para instalação adaptativa (greenfield/legacy/merge), `memory-bootstrap` para início de sessão, `memory-debrief` para fim de unidade de trabalho.

Suporte multi-agente via convenção `AGENT.md` com `CLAUDE.md` como redirect mínimo para o Claude Code.

Workflow de merge e rebase com `.gitattributes` configurando driver `ours` para artefatos voláteis e detecção de colisões de IDs via `audit.py --check-collisions`.

Manual do usuário (`USER_GUIDE.md`) cobrindo instalação, fluxo típico, comandos importantes, resolução de problemas e trabalho em time.

Versionamento semântico com `VERSION` e `CHANGELOG.md`.
