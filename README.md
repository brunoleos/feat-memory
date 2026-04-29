# agent-memory

Memória persistente para agentes LLM como CLI Python. Instale com `pipx`, rode `agent-memory deploy <projeto>`, e peça ao agente para configurar.

## O que é isso

Quatro artefatos versionados que dão a um agente LLM tudo que ele precisa para retomar trabalho em um projeto sem reler todo o código a cada sessão. Cada artefato responde uma pergunta diferente, com um ciclo de mutação diferente.

| Artefato | Pergunta | Mutação |
|---|---|---|
| `AGENT.md` | Sob quais regras construímos? | Rara |
| `manifest/` | O que existe hoje no sistema? | Append-only |
| `STATE.md` | Onde estamos agora? | Reescrita bounded |
| `decisions/` | Por que escolhemos assim? | Imutável + supersede |

## Instalação

Instale a CLI uma vez na sua máquina (a partir do clone do projeto):

```bash
git clone https://github.com/brunoleos/agent-memory.git ~/dev/agent-memory
pipx install -e ~/dev/agent-memory
```

A flag `-e` é editable install: o binário `agent-memory` no seu PATH lê o código direto do clone, então `git pull` no clone atualiza a CLI imediatamente em todos os projetos. Detalhes desse modo estão em [USER_GUIDE.md](USER_GUIDE.md).

Em qualquer projeto consumidor, rode:

```bash
agent-memory deploy /caminho/do/projeto
```

Isso monta `AGENT.md`, `CLAUDE.md`, `STATE.md`, `manifest/`, `decisions/`, `skills/`, `.gitattributes`, instala o pre-commit hook, e adiciona `.agent-memory-deploy/` ao `.gitignore` (estado transiente do deploy; ver "Comportamento com arquivos pré-existentes").

Depois, abra uma sessão com seu agente preferido (Claude Code, Cursor, ou outro que reconheça `AGENT.md`) e peça:

```text
instale a metodologia neste projeto
```

A skill `memory-deploy` detecta se o projeto é greenfield (novo, pouco código) ou legacy (com história substancial), conduz personalização em diálogo curto para greenfield, ou gênese retroativa em quatro fases para legacy.

Para projetos greenfield, a skill faz perguntas específicas sobre identidade do projeto, stack, restrições não-negociáveis e foco inicial. Em alguns minutos você tem `AGENT.md` e `STATE.md` personalizados, prontos para o primeiro commit.

Para projetos legacy, a skill conduz gênese retroativa em quatro fases sequenciais com revisão humana entre cada uma: AGENT.md a partir do código existente, ADRs candidatos a partir do git log, Manifest a partir dos entrypoints públicos, e STATE.md inicial com auditoria. Cada fase apresenta drafts para sua aprovação antes de gravar.

## Comportamento com arquivos pré-existentes

Quando o `AGENT.md` ou o `CLAUDE.md` já existem na raiz do projeto, o `agent-memory deploy` não os sobrescreve. Em vez disso, ele preserva o conteúdo existente e registra os arquivos em uma fila de merge pendente em `<projeto>/.agent-memory-deploy/merge-queue`, salvando uma cópia do template novo em `<projeto>/.agent-memory-deploy/pending/<arquivo>.new`. A skill `memory-deploy` então mescla o conteúdo existente com o template novo, preservando customizações do usuário e adicionando apenas estrutura faltante.

O diretório `.agent-memory-deploy/` é gitignored automaticamente e existe apenas durante o handoff entre o `agent-memory deploy` e a skill. Após o merge ser resolvido, ele pode ser removido.

O `STATE.md` segue semântica diferente: como o conteúdo dele é volátil por construção, não há valor real em mesclar. Se já existe, é simplesmente pulado.

As skills em `skills/` são sempre reescritas a cada deploy, porque elas são conteúdo de metodologia (não de usuário). Se você quiser uma skill customizada, copie-a para um nome diferente (`skills/memory-debrief` → `skills/my-debrief`) — a versão renomeada é preservada. O `.gitattributes` segue a mesma lógica via bloco com sentinelas: o que estiver fora do bloco é preservado, o bloco em si é refrescado.

A flag `--force` sobrescreve tudo sem merge, útil quando você quer descartar customizações e voltar aos templates limpos. A flag `--no-merge` pula `AGENT.md` e `CLAUDE.md` se já existem (sem mesclar nem sobrescrever), útil em CI onde a personalização não se aplica.

## Versionamento e atualizações

O pacote tem versionamento semântico em `VERSION` (lido pelo `pyproject.toml`) e changelog em [CHANGELOG.md](CHANGELOG.md). Cada release publicada em <https://github.com/brunoleos/agent-memory/releases> corresponde a uma tag `vX.Y.Z`. Para descobrir a versão instalada, rode `agent-memory --version` (em breve) ou `pipx list | grep agent-memory`.

Em editable install, atualizar é simplesmente `git pull` no clone:

```bash
cd ~/dev/agent-memory
git pull
```

A CLI passa a refletir a versão nova imediatamente em todos os projetos consumidores. Para fixar em uma tag específica:

```bash
cd ~/dev/agent-memory
git fetch --tags
git checkout v0.3.0
```

Para reaplicar templates e skills em um projeto consumidor após upgrade, rode `agent-memory deploy <projeto>` novamente — ele é idempotente e re-roda a lógica de merge para `AGENT.md` e `CLAUDE.md` (preservando suas customizações), atualiza skills e `.gitattributes`, garante a entrada em `.gitignore`, e reinstala o pre-commit hook.

Quando o pacote estiver publicado na PyPI (planejado), o caminho de instalação para usuários finais será `pipx install agent-memory` (sem `-e`), e atualização será `pipx upgrade agent-memory`.

## Modo programático

Em CI ou automação sem intervenção humana, o `agent-memory deploy` pode ser invocado direto sem passar pela skill. Em ambientes onde personalização não se aplica, use `--no-merge` para evitar criar fila de merge pendente em `AGENT.md`/`CLAUDE.md`.

```bash
agent-memory deploy <projeto>             # padrão: merge AGENT/CLAUDE se existem
agent-memory deploy <projeto> --no-merge  # pula AGENT/CLAUDE existentes (sem merge)
agent-memory deploy <projeto> --force     # sobrescreve TUDO sem merge
agent-memory deploy <projeto> --no-hooks  # pula instalação de git hooks
```

A escolha entre skill e comando direto reflete os dois modos de uso. Para humanos adotando a metodologia em um projeto real, a skill é o caminho. Para automação que apenas precisa da estrutura mecânica, o comando direto basta.

## Portabilidade

Todas as ferramentas estão escritas em Python 3.10 ou superior, sem dependência de shell scripts. O pacote roda em Linux, macOS e Windows nativamente, sem necessidade de WSL ou outras camadas de compatibilidade. A única dependência externa é PyYAML, declarada em `pyproject.toml` e instalada automaticamente pelo `pipx`.

## Estrutura do pacote

```text
agent-memory/                         # clone do projeto na sua máquina
├── pyproject.toml                    # metadados do pacote
├── README.md                         # este arquivo
├── USER_GUIDE.md                     # manual prático para usuários
├── METHODOLOGY.md                    # doutrina completa
├── FUTURE_IMPROVEMENTS.md            # roadmap de extensões
├── CHANGELOG.md                      # histórico de versões
├── VERSION                           # versão semântica atual (lida por pyproject)
├── src/
│   └── agent_memory/                 # pacote Python
│       ├── __init__.py
│       ├── cli.py                    # entrypoint: agent-memory ...
│       ├── deploy.py                 # subcomando deploy
│       ├── audit.py                  # subcomando audit
│       ├── propose_adr.py            # subcomando propose-adr
│       ├── migrate.py                # subcomando migrate
│       ├── install_hooks.py          # helper de instalação de hooks
│       └── data/                     # package data (vai no wheel)
│           ├── templates/            # AGENT.md, CLAUDE.md, STATE.md, .gitattributes
│           ├── skills/               # memory-deploy, memory-bootstrap, memory-debrief
│           └── hooks/                # pre-commit
├── tests/                            # suite pytest
└── examples/                         # exemplos pedagógicos (não vão no wheel)
    ├── manifest/features/F-0001-vector-similarity-search.md
    ├── decisions/0001-record-architecture-decisions.md
    └── decisions/0002-cosine-similarity-default.md
```

## Estrutura final no project root

Depois da instalação, o seu repositório tem isto. Os artefatos versionados em Git são `AGENT.md`, `CLAUDE.md`, `STATE.md`, `manifest/`, `decisions/`, `skills/`, `.gitattributes`, e o bloco em `.gitignore`. O diretório `.agent-memory-deploy/` é gitignored e transiente.

```text
seu-projeto/
├── .gitignore                        # contém bloco com .agent-memory-deploy/
├── .gitattributes                    # bloco com sentinelas (regras de merge)
├── .agent-memory-deploy/             # gitignored — só existe durante handoff de merge
├── AGENT.md                          # constituição
├── CLAUDE.md                         # redirect para AGENT.md (Claude Code)
├── STATE.md                          # foco da sessão
├── skills/
│   ├── memory-deploy/SKILL.md
│   ├── memory-bootstrap/SKILL.md
│   └── memory-debrief/SKILL.md
├── manifest/
│   ├── INDEX.md                      # gerado por agent-memory audit
│   └── features/
│       └── (vazio até primeira feature)
├── decisions/
│   ├── INDEX.md                      # gerado por agent-memory audit
│   ├── proposals/                    # drafts de agent-memory propose-adr
│   └── (vazio até primeiro ADR)
└── (seu código de sempre)
```

## Operação diária

As três skills cobrem três momentos qualitativamente diferentes do uso da metodologia. Cada uma tem triggers próprios e instruções autoritativas no respectivo `SKILL.md`. O agente que entende essas skills (Claude Code via `CLAUDE.md`, Cursor via `AGENT.md`, e outros) descobre os triggers a partir do `description` no frontmatter de cada skill.

A skill `memory-deploy` cobre a adoção inicial, executada uma única vez por projeto. Ela ativa quando o usuário pede para instalar a metodologia e conduz tanto greenfield quanto legacy, conforme detectado.

A skill `memory-bootstrap` cobre o início de cada sessão de trabalho. Frases como "onde paramos" ou "qual o status" ativam a skill, que carrega o contexto eficientemente e apresenta um briefing tático antes de prosseguir.

A skill `memory-debrief` é a mais usada no dia-a-dia. Frases como "vou commitar" ou "atualize o STATE" ativam a skill, que examina o diff, atualiza o Manifest, reescreve o State, e gera proposta de ADR se necessário. Invoque-a antes de cada commit relevante.

## Comandos úteis

A auditoria valida todos os artefatos e gera os índices automaticamente. Ela é executada também pelo pre-commit hook em modo strict.

```bash
agent-memory audit                # relatório + índices
agent-memory audit --strict       # warnings viram errors
agent-memory audit --json         # output para CI
```

O gerador de propostas examina o diff atual e detecta sinais de mudança arquitetural não-trivial, gerando draft em `decisions/proposals/` para revisão. É invocado pela skill `memory-debrief` mas pode ser chamado diretamente.

```bash
agent-memory propose-adr             # examina HEAD~1..HEAD
agent-memory propose-adr --staged    # mudanças staged
agent-memory propose-adr --prompt    # prompt para LLM
```

O detector de candidatos para gênese retroativa é invocado pela skill `memory-deploy` na fase 2 de projetos legacy. Pode ser chamado diretamente para inspeção do histórico.

```bash
agent-memory migrate --limit 200
```

## Documentação

A documentação está dividida em três níveis. O [USER_GUIDE.md](USER_GUIDE.md) é o manual prático para usuários, cobrindo instalação, fluxo de trabalho típico, comandos importantes, resolução de problemas comuns, e trabalho em time. Comece por ele se você está adotando a metodologia pela primeira vez.

A doutrina técnica completa está em [METHODOLOGY.md](METHODOLOGY.md), incluindo o esquema de cada artefato, a notação EARS para critérios de aceitação, o protocolo do agente, as métricas de auditoria, o workflow de merge e rebase, e casos de borda. Use-o como referência quando precisa entender por que algo funciona como funciona.

O roadmap está em [FUTURE_IMPROVEMENTS.md](FUTURE_IMPROVEMENTS.md), registrando extensões implementadas (com link reverso para quando foram adicionadas), planejadas (organizadas por horizonte), e explicitamente rejeitadas (com a razão da rejeição registrada).
