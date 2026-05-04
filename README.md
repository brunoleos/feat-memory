# agent-memory

Memória persistente para agentes LLM como CLI Python. Instale com `pipx`, rode `agent-memory deploy <projeto>`, e peça ao agente para configurar.

## O que é isso

Quatro artefatos versionados que dão a um agente LLM tudo que ele precisa para retomar trabalho em um projeto sem reler todo o código a cada sessão. Cada artefato responde uma pergunta diferente, com um ciclo de mutação diferente.

| Artefato | Pergunta | Mutação |
|---|---|---|
| `AGENT.md` | Sob quais regras construímos? | Rara |
| `.agent-memory/manifest/` | O que existe hoje no sistema? | Append-only |
| `.agent-memory/STATE.md` | Onde estamos agora? | Reescrita bounded |
| `.agent-memory/decisions/` | Por que escolhemos assim? | Imutável + supersede |

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

Isso monta `AGENT.md`, `CLAUDE.md`, `.agent-memory/STATE.md`, `.agent-memory/manifest/`, `.agent-memory/decisions/`, `skills/`, `.gitattributes`, e instala o pre-commit hook.

Depois, abra uma sessão com seu agente preferido (Claude Code, Cursor, ou outro que reconheça `AGENT.md`) e peça:

```text
instale a metodologia neste projeto
```

A skill `memory-deploy` detecta se o projeto é greenfield (novo, pouco código) ou legacy (com história substancial). Em greenfield, ela apenas executa o deploy mecânico — identidade, restrições, convenções e demais conteúdos específicos do projeto são autoria do mantenedor humano, escritos diretamente no `AGENT.md` quando ele decidir que vale registrar.

Para projetos legacy, a skill conduz adicionalmente gênese retroativa em três fases sequenciais com revisão humana entre cada uma: ADRs candidatos a partir do git log, Manifest a partir dos entrypoints públicos, e `.agent-memory/STATE.md` inicial. A skill nunca escreve no corpo da `AGENT.md` fora do bloco delimitado por sentinelas — esse bloco é gerenciado mecanicamente pelo `agent-memory deploy`.

## Comportamento com arquivos pré-existentes

O `agent-memory deploy` é idempotente em todas as superfícies que ele instala. A `AGENT.md` carrega um bloco delimitado por sentinelas markdown:

```markdown
<!-- >>> agent-memory >>> -->
## agent-memory
[instruções de uso da metodologia, refrescadas a cada deploy]
<!-- <<< agent-memory <<< -->
```

Quando o `AGENT.md` já existe, o deploy só toca o conteúdo entre essas sentinelas — todo o resto (frontmatter, seções específicas do projeto, comentários do usuário) é preservado. Quando ainda não existe, o template completo é escrito (frontmatter scaffold + bloco). O `CLAUDE.md` (redirect mínimo `@AGENT.md`) é copiado se ausente e deixado quieto se existe.

O `.agent-memory/STATE.md` segue semântica diferente: como o conteúdo dele é volátil por construção, não há valor real em mesclar. Se já existe, é simplesmente pulado.

As skills em `skills/` são sempre reescritas a cada deploy, porque elas são conteúdo de metodologia (não de usuário). Se você quiser uma skill customizada, copie-a para um nome diferente (`skills/memory-debrief` → `skills/my-debrief`) — a versão renomeada é preservada. O `.gitattributes` segue a mesma lógica via bloco com sentinelas: o que estiver fora do bloco é preservado, o bloco em si é refrescado.

A flag `--force` reescreve `AGENT.md`, `CLAUDE.md` e `.agent-memory/STATE.md` inteiros a partir do template, descartando conteúdo do usuário fora do bloco. A flag `--no-merge` pula a refresh do bloco em `AGENT.md`/`CLAUDE.md` existentes (útil em CI onde nenhuma modificação é desejada).

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

Para reaplicar templates e skills em um projeto consumidor após upgrade, rode `agent-memory deploy <projeto>` novamente — ele é idempotente: refresca o bloco com sentinelas em `AGENT.md` (preservando todo o resto), atualiza skills e `.gitattributes`, garante a entrada em `.gitignore`, e reinstala o pre-commit hook.

Quando o pacote estiver publicado na PyPI (planejado), o caminho de instalação para usuários finais será `pipx install agent-memory` (sem `-e`), e atualização será `pipx upgrade agent-memory`.

## Modo programático

Em CI ou automação sem intervenção humana, o `agent-memory deploy` pode ser invocado direto sem passar pela skill. Em ambientes onde refresh do bloco não é desejada, use `--no-merge`.

```bash
agent-memory deploy <projeto>             # padrão: refresca bloco em AGENT.md, copia CLAUDE.md se ausente
agent-memory deploy <projeto> --no-merge  # pula AGENT/CLAUDE existentes (sem refresh do bloco)
agent-memory deploy <projeto> --force     # reescreve AGENT/CLAUDE/STATE inteiros do template
agent-memory deploy <projeto> --no-hooks  # pula instalação de git hooks
```

A escolha entre skill e comando direto reflete os dois modos de uso. Para humanos adotando a metodologia em um projeto real, a skill é o caminho (em legacy ela faz a gênese retroativa de ADRs e Manifest, que o comando direto não faz). Para automação que apenas precisa da estrutura mecânica, o comando direto basta.

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
│           ├── skills/               # memory-deploy, memory-bootstrap, memory-debrief, memory-pull-brief
│           └── hooks/                # pre-commit
├── tests/                            # suite pytest
└── examples/                         # exemplos pedagógicos (não vão no wheel)
    ├── manifest/features/F-0001-vector-similarity-search.md
    ├── decisions/0001-record-architecture-decisions.md
    └── decisions/0002-cosine-similarity-default.md
```

## Estrutura final no project root

Depois da instalação, o seu repositório tem isto. Os artefatos versionados em Git são `AGENT.md`, `CLAUDE.md`, `.agent-memory/STATE.md`, `.agent-memory/manifest/`, `.agent-memory/decisions/`, `skills/`, `.gitattributes`, e o bloco em `.gitignore`.

```text
seu-projeto/
├── .gitignore                        # contém bloco com regras agent-memory
├── .gitattributes                    # bloco com sentinelas (regras de merge)
├── AGENT.md                          # constituição (com bloco agent-memory delimitado por sentinelas)
├── CLAUDE.md                         # redirect para AGENT.md (Claude Code)
├── skills/
│   ├── memory-deploy/SKILL.md
│   ├── memory-bootstrap/SKILL.md
│   ├── memory-debrief/SKILL.md
│   └── memory-pull-brief/SKILL.md
├── .agent-memory/
│   ├── STATE.md                      # foco da sessão
│   ├── manifest/
│   │   ├── INDEX.md                  # gerado por agent-memory audit
│   │   └── features/
│   │       └── (vazio até primeira feature)
│   └── decisions/
│       ├── INDEX.md                  # gerado por agent-memory audit
│       ├── proposals/                # drafts de agent-memory propose-adr
│       └── (vazio até primeiro ADR)
└── (seu código de sempre)
```

## Operação diária

As quatro skills cobrem quatro momentos qualitativamente diferentes do uso da metodologia. Cada uma tem triggers próprios e instruções autoritativas no respectivo `SKILL.md`. O agente que entende essas skills (Claude Code via `CLAUDE.md`, Cursor via `AGENT.md`, e outros) descobre os triggers a partir do `description` no frontmatter de cada skill.

A skill `memory-deploy` cobre a adoção inicial, executada uma única vez por projeto. Ela ativa quando o usuário pede para instalar a metodologia e conduz tanto greenfield quanto legacy, conforme detectado.

A skill `memory-bootstrap` cobre o início de cada sessão de trabalho. Frases como "onde paramos" ou "qual o status" ativam a skill, que carrega o contexto eficientemente e apresenta um briefing tático antes de prosseguir.

A skill `memory-debrief` é a mais usada no dia-a-dia. Frases como "vou commitar" ou "atualize o STATE" ativam a skill, que examina o diff, atualiza o Manifest, reescreve o State, e gera proposta de ADR se necessário. Invoque-a antes de cada commit relevante.

A skill `memory-pull-brief` cobre o quarto momento crítico: depois de `git pull` que trouxe commits de colegas. Frases como "o que veio do pull" ou "brifa as mudanças do main" ativam a skill, que examina o diff trazido, identifica mudanças semânticas em `.agent-memory/manifest/`, `.agent-memory/decisions/` e no bloco metodológico de `AGENT.md`, e propõe ajustes em `.agent-memory/STATE.md` para ressincronizar o foco local. É read-only sobre `.agent-memory/manifest/` e `.agent-memory/decisions/` — esses já vieram corretos do pull.

## Comandos úteis

A auditoria valida todos os artefatos e gera os índices automaticamente. Ela é executada também pelo pre-commit hook em modo strict.

```bash
agent-memory audit                # relatório + índices
agent-memory audit --strict       # warnings viram errors
agent-memory audit --json         # output para CI
```

O gerador de propostas examina o diff atual e detecta sinais de mudança arquitetural não-trivial, gerando draft em `.agent-memory/decisions/proposals/` para revisão. É invocado pela skill `memory-debrief` mas pode ser chamado diretamente.

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
