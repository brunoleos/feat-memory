# Changelog

Todas as mudanças notáveis a esta metodologia são registradas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/) e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.5.0] - 2026-04-30

### Adicionado

Quarta skill `memory-pull-brief` (F-0009) cobre o gap cognitivo pós-pull em projetos cliente. Quando o desenvolvedor faz `git pull` e recebe commits de colegas, a skill examina o diff trazido, identifica mudanças semânticas em `manifest/features/`, `decisions/` e no bloco metodológico de `AGENT.md`, e propõe ajustes em `STATE.md` (remoção de IDs em `active_*` cuja semântica upstream invalida o foco local, entrada nova no buffer `Recent`). É read-only sobre `manifest/` e `decisions/` por design — esses já vieram corretos do pull, escrever neles seria reverter trabalho de colegas. Trigger duplo: manual (frases como "o que veio do pull", "brifa as mudanças do main") e por delegação a partir de `memory-bootstrap` quando o último commit é merge que tocou artefatos.

Decisão formalizada em [ADR-0012](.agent-memory/decisions/0012-skill-memory-pull-brief.md).

### Mudado

Skill `memory-bootstrap` (F-0007) ganha passo de detecção de merge tocando artefatos: após o `agent-memory audit` regenerar índices, se o merge moveu `manifest/features/`, `decisions/` ou o bloco sentinela de `AGENT.md`, a bootstrap delega para `memory-pull-brief` antes do briefing tático. Sem esse trigger, comportamento prévio é preservado.

Bloco "Skills disponíveis" do template `AGENT.md` atualizado de "três skills" para "quatro skills" e ganha parágrafo sobre `memory-pull-brief`. Refresh automático no próximo `agent-memory deploy` em projetos consumidores.

## [0.4.0] - 2026-04-30

### Mudado

**BREAKING.** O `agent-memory deploy` passa a gerenciar a metodologia em `AGENT.md` exclusivamente dentro de um bloco delimitado por sentinelas markdown (`<!-- >>> agent-memory >>> -->` / `<!-- <<< agent-memory <<< -->`). Refresh é idempotente: re-deploy substitui só o bloco, todo o resto do arquivo é preservado byte-a-byte. Identidade, restrições, convenções e qualquer outro conteúdo específico do projeto vivem fora do bloco e nunca são tocados pelo deploy ou pela skill `memory-deploy`. O comportamento anterior de "merge inteligente" baseado em comparação de headings (introduzido em v0.3.1) é abandonado em favor desta abordagem mais simples.

A skill `memory-deploy` perde a Etapa 3 (merge) e a Etapa 4 (personalização) inteiras. Em greenfield, a skill apenas roda o deploy mecânico — não pergunta sobre identidade/stack/restrições nem popula o frontmatter. Em legacy, conduz três fases de gênese retroativa: ADRs do git log, Manifest dos entrypoints, e `STATE.md::Current` descrevendo a gênese. A skill nunca toca em `AGENT.md` fora do bloco.

Decisão formalizada em [ADR-0011](.agent-memory/decisions/0011-deploy-replaces-agent-md-block-via-sentinels.md), que supersede [ADR-0010](.agent-memory/decisions/0010-merge-separates-methodology-from-project-sections.md).

### Removido

Mecanismo de merge-queue (`<projeto>/.agent-memory-deploy/merge-queue` e `pending/`) eliminado. O deploy resolve o bloco da `AGENT.md` diretamente via sentinelas, sem handoff intermediário. Diretório legado é removido automaticamente na primeira execução pós-upgrade.

### Migração de 0.3.x → 0.4.0

Para projetos consumidores que estão na v0.3.x:

```bash
agent-memory deploy /caminho/projeto
```

O bloco com sentinelas é anexado ao fim do `AGENT.md` existente. O conteúdo de metodologia que estava em seções H2 separadas (`## Skills disponíveis`, `## Como retomar trabalho`) e no parágrafo introdutório fica duplicado — agora dentro do bloco e ainda nas seções antigas. Remova manualmente as seções antigas (basta deletar tudo entre `## Skills disponíveis` e `## Como retomar trabalho` inclusive, se essas eram as únicas seções de metodologia preexistentes).

## [0.3.1] - 2026-04-30

### Corrigido

Skill `memory-deploy` (Etapa 3) tinha bug de concatenação no merge do `AGENT.md`: quando o template novo carregava `## Identidade` como placeholder e o existente já tinha conteúdo real, a heurística "adiciona seções novas ao final" produzia arquivo com seções duplicadas. O algoritmo de merge foi reescrito para separar seções de metodologia (sincronizadas a partir do template) de seções de projeto (preservadas a partir do existente), com ordem fixa do resultado: intro → projeto → Skills → Como retomar trabalho.

### Mudado

Template `AGENT.md` deixa de carregar placeholders para as seções de projeto (`## Identidade`, `## Restrições não-negociáveis`, `## Convenções de código`) — apenas um comentário HTML marca o ponto de inserção. A skill `memory-deploy` escreve essas seções a partir da investigação do repositório durante a Etapa 4 (personalização ou gênese retroativa). Decisão formalizada em [ADR-0010](.agent-memory/decisions/0010-merge-separates-methodology-from-project-sections.md).

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
