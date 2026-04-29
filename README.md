# `.agent-memory/`

Pacote autocontido de memória persistente para agentes LLM. Cole esta pasta inteira na raiz do seu projeto e peça ao agente para instalar a metodologia.

## O que é isso

Quatro artefatos versionados que dão a um agente LLM tudo que ele precisa para retomar trabalho em um projeto sem reler todo o código a cada sessão. Cada artefato responde uma pergunta diferente, com um ciclo de mutação diferente.

| Artefato | Pergunta | Mutação |
|---|---|---|
| `AGENT.md` | Sob quais regras construímos? | Rara |
| `manifest/` | O que existe hoje no sistema? | Append-only |
| `STATE.md` | Onde estamos agora? | Reescrita bounded |
| `decisions/` | Por que escolhemos assim? | Imutável + supersede |

## Instalação

A instalação tem dois passos. Primeiro, copie a pasta `.agent-memory/` para a raiz do seu projeto. Segundo, peça ao agente para instalar a metodologia com uma frase como "instale a metodologia neste projeto" ou "configure o agent-memory aqui".

```bash
# 1. Cole esta pasta inteira na raiz do projeto
cp -r path/to/agent-memory/.agent-memory ./

# 2. Inicie uma sessão com o agente e peça:
#    "instale a metodologia neste projeto"
```

A partir daí, a skill `memory-deploy` assume o controle. Ela detecta automaticamente se o seu projeto é greenfield (novo, pouco código) ou legacy (com história substancial e código de produção), executa o `deploy.py` para estabelecer a estrutura mecânica, e conduz a personalização apropriada para cada caso.

Para projetos greenfield, a skill conduz personalização em diálogo curto, fazendo perguntas específicas sobre identidade do projeto, stack, restrições não-negociáveis e foco inicial. Em alguns minutos você tem o `AGENT.md` e o `STATE.md` personalizados, prontos para o primeiro commit.

Para projetos legacy, a skill conduz gênese retroativa em quatro fases sequenciais com revisão humana entre cada uma: AGENT.md a partir do código existente, ADRs candidatos a partir do git log, Manifest a partir dos entrypoints públicos, e STATE.md inicial com auditoria. Cada fase apresenta drafts para sua aprovação antes de gravar.

## Comportamento com arquivos pré-existentes

Quando o `AGENT.md` ou o `CLAUDE.md` já existem na raiz do projeto, o `deploy.py` não os sobrescreve. Em vez disso, ele preserva o conteúdo existente e registra os arquivos em uma fila de merge pendente (`.agent-memory/.merge-queue`), salvando uma cópia do template novo para referência (`.agent-memory/.pending-merge/<arquivo>.new`). A skill `memory-deploy` então mescla o conteúdo existente com o template novo, preservando customizações do usuário e adicionando apenas estrutura faltante.

O `STATE.md` segue semântica diferente: como o conteúdo dele é volátil por construção, não há valor real em mesclar. Se já existe, é simplesmente pulado. As skills em `skills/` também são puladas se já existem.

A flag `--force` sobrescreve tudo sem merge, útil quando você quer descartar customizações e voltar aos templates limpos. A flag `--no-merge` pula arquivos existentes sem sobrescrever nem mesclar, restaurando o comportamento de "skip se existe", útil em CI onde a personalização não se aplica.

## Versionamento e atualizações

O pacote tem versionamento semântico em `VERSION` e changelog em `CHANGELOG.md`. Quando você instala em um projeto, a versão é registrada em `.agent-memory/.installed-version` (não versionado no Git), permitindo saber qual versão está em uso e gerenciar atualizações.

Para atualizar a metodologia em um projeto, configure o upstream em `.agent-memory/.upstream` e rode `python .agent-memory/update.py`. O upstream pode ser um repositório Git remoto, uma tag específica desse repositório, ou um caminho local (útil durante desenvolvimento da própria metodologia).

```bash
# Configure o upstream (faça uma vez por clone)
echo "git+https://github.com/usuario/agent-memory.git" > .agent-memory/.upstream

# Verifique se há atualização
python .agent-memory/update.py --check

# Aplique a atualização
python .agent-memory/update.py
```

O `update.py` baixa a versão mais recente do upstream, substitui o conteúdo de `.agent-memory/` preservando arquivos de configuração local (`.installed-version`, `.upstream`, fila de merge pendente), e re-roda o `deploy.py` com a lógica de merge para propagar mudanças aos artefatos do projeto sem perder customizações do `AGENT.md` ou do `CLAUDE.md`.

O arquivo `.upstream.example` no pacote documenta as opções de configuração. O fluxo de update reusa toda a infraestrutura de merge do deploy, garantindo consistência semântica entre instalação inicial e atualizações subsequentes.

## Modo programático

Se você precisa instalar a metodologia em CI ou em automação sem intervenção humana, o `deploy.py` pode ser invocado diretamente. Em ambientes onde personalização não se aplica, use `--no-merge` para evitar a fila de merge pendente.

```bash
python .agent-memory/deploy.py             # padrão: merge AGENT/CLAUDE
python .agent-memory/deploy.py --no-merge  # pula arquivos existentes
python .agent-memory/deploy.py --force     # sobrescreve TUDO sem merge
python .agent-memory/deploy.py --no-hooks  # pula instalação de git hooks
```

A escolha entre skill e script reflete os dois modos de uso. Para humanos adotando a metodologia em um projeto real, a skill é o caminho. Para automação que apenas precisa da estrutura mecânica, o script direto basta.

## Portabilidade

Todas as ferramentas estão escritas em Python 3.10 ou superior, sem dependência de shell scripts. O pacote roda em Linux, macOS e Windows nativamente, sem necessidade de WSL ou outras camadas de compatibilidade. A única dependência externa é PyYAML (`pip install pyyaml`), que o `audit.py` reporta com mensagem clara se ausente.

## Estrutura do pacote

```
.agent-memory/
├── README.md                      # este arquivo
├── USER_GUIDE.md                  # manual prático para usuários
├── METHODOLOGY.md                 # doutrina completa
├── FUTURE_IMPROVEMENTS.md         # roadmap de extensões
├── CHANGELOG.md                   # histórico de versões
├── VERSION                        # versão semântica atual
├── .upstream.example              # template de configuração de upstream
├── deploy.py                      # script mecânico (chamado pela skill ou direto)
├── update.py                      # atualização a partir do upstream
│
├── templates/                     # copiados para o project root no deploy
│   ├── AGENT.md
│   ├── CLAUDE.md
│   ├── STATE.md
│   └── .gitattributes
│
├── skills/                        # copiadas para /skills/ no deploy
│   ├── memory-deploy/SKILL.md
│   ├── memory-bootstrap/SKILL.md
│   └── memory-debrief/SKILL.md
│
├── tools/                         # ferramentas operacionais
│   ├── audit.py                   # validação + geração de índices
│   ├── migrate.py                 # detector de candidatos a ADR (legacy)
│   ├── propose-adr.py             # gerador de propostas de ADR (uso normal)
│   ├── install_hooks.py           # instala git hooks
│   └── hooks/
│       └── pre-commit             # bloqueia commits inválidos (Python)
│
└── examples/                      # exemplos pedagógicos (não copiados)
    ├── manifest/features/F-0001-vector-similarity-search.md
    ├── decisions/0001-record-architecture-decisions.md
    └── decisions/0002-cosine-similarity-default.md
```

A pasta `.agent-memory/` permanece versionada no projeto após a instalação. Os tools são invocados de lá, as skills são carregadas pelos agentes a partir de lá, e a documentação de referência fica acessível.

## Estrutura final no project root

Depois da instalação:

```
seu-projeto/
├── .agent-memory/                 # o pacote completo (continua aqui)
├── AGENT.md                       # constituição (deployada de templates/)
├── CLAUDE.md                      # redirect para AGENT.md (Claude Code)
├── STATE.md                       # foco da sessão (deployado de templates/)
├── skills/                        # skills (deployadas de .agent-memory/skills/)
│   ├── memory-deploy/SKILL.md
│   ├── memory-bootstrap/SKILL.md
│   └── memory-debrief/SKILL.md
├── manifest/
│   ├── INDEX.md                   # gerado por audit.py
│   └── features/
│       └── (vazio até primeira feature)
├── decisions/
│   ├── INDEX.md                   # gerado por audit.py
│   ├── proposals/                 # drafts de propose-adr.py
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
python .agent-memory/tools/audit.py              # relatório + índices
python .agent-memory/tools/audit.py --strict     # warnings viram errors
python .agent-memory/tools/audit.py --json       # output para CI
```

O gerador de propostas examina o diff atual e detecta sinais de mudança arquitetural não-trivial, gerando draft em `decisions/proposals/` para revisão. É invocado pela skill `memory-debrief` mas pode ser chamado diretamente.

```bash
python .agent-memory/tools/propose-adr.py             # examina HEAD~1..HEAD
python .agent-memory/tools/propose-adr.py --staged    # mudanças staged
python .agent-memory/tools/propose-adr.py --prompt    # prompt para LLM
```

O detector de candidatos para gênese retroativa é invocado pela skill `memory-deploy` na fase 2 de projetos legacy. Pode ser chamado diretamente para inspeção do histórico.

```bash
python .agent-memory/tools/migrate.py --limit 200
```

## Documentação

A documentação está dividida em três níveis. O `USER_GUIDE.md` é o manual prático para usuários, cobrindo instalação, fluxo de trabalho típico, comandos importantes, resolução de problemas comuns, e trabalho em time. Comece por ele se você está adotando a metodologia pela primeira vez.

A doutrina técnica completa está em `METHODOLOGY.md`, incluindo o esquema de cada artefato, a notação EARS para critérios de aceitação, o protocolo do agente, as métricas de auditoria, o workflow de merge e rebase, e casos de borda. Use-o como referência quando precisa entender por que algo funciona como funciona.

O roadmap está em `FUTURE_IMPROVEMENTS.md`, registrando extensões implementadas (com link reverso para quando foram adicionadas), planejadas (organizadas por horizonte), e explicitamente rejeitadas (com a razão da rejeição registrada).
