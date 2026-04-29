# `.agent-memory/`

Pacote autocontido de memória persistente para agentes LLM. Cole esta pasta inteira na raiz do seu projeto e peça ao agente para instalar a metodologia.

Repositório oficial: <https://github.com/brunoleos/agent-memory>. Releases e changelog em <https://github.com/brunoleos/agent-memory/releases>.

## O que é isso

Quatro artefatos versionados que dão a um agente LLM tudo que ele precisa para retomar trabalho em um projeto sem reler todo o código a cada sessão. Cada artefato responde uma pergunta diferente, com um ciclo de mutação diferente.

| Artefato | Pergunta | Mutação |
|---|---|---|
| `AGENT.md` | Sob quais regras construímos? | Rara |
| `manifest/` | O que existe hoje no sistema? | Append-only |
| `STATE.md` | Onde estamos agora? | Reescrita bounded |
| `decisions/` | Por que escolhemos assim? | Imutável + supersede |

## Instalação

A instalação tem dois passos: trazer a pasta `.agent-memory/` para a raiz do seu projeto e pedir ao agente para configurá-la. A pasta inteira fica versionada junto com o seu projeto.

### 1. Trazer a pasta para o projeto

Escolha um dos três caminhos. Os três produzem o mesmo resultado; mude apenas em qual versão você fica fixado.

**a) Clone direto da release mais recente (recomendado).** Use a tag estável; `--depth 1` evita baixar o histórico inteiro:

```bash
git clone --depth 1 --branch v0.1.0 \
  https://github.com/brunoleos/agent-memory.git /tmp/agent-memory
cp -r /tmp/agent-memory/.agent-memory ./
rm -rf /tmp/agent-memory
```

Ajuste `v0.1.0` para a tag listada em <https://github.com/brunoleos/agent-memory/releases>.

**b) Download do tarball de uma release.** Útil se você não quer Git no caminho:

```bash
curl -L https://github.com/brunoleos/agent-memory/archive/refs/tags/v0.1.0.tar.gz \
  | tar -xz --strip-components=1 -C ./ agent-memory-0.1.0/.agent-memory
```

**c) Seguir a `main` em vez de uma tag.** Recomendado apenas durante experimentação:

```bash
git clone --depth 1 https://github.com/brunoleos/agent-memory.git /tmp/agent-memory
cp -r /tmp/agent-memory/.agent-memory ./
rm -rf /tmp/agent-memory
```

A pasta `.agent-memory/` que você acabou de copiar já contém tudo: scripts, skills, templates e este README. Ela é autocontida — o repositório de onde você clonou só é necessário se você quiser receber atualizações depois (ver "Versionamento e atualizações" abaixo).

### 2. Pedir ao agente para configurar

Inicie uma sessão com o agente e diga:

```
instale a metodologia neste projeto
```

A partir daí, a skill `memory-deploy` assume o controle. Ela detecta automaticamente se o seu projeto é greenfield (novo, pouco código) ou legacy (com história substancial e código de produção), executa o `deploy.py` para estabelecer a estrutura mecânica, e conduz a personalização apropriada para cada caso.

Para projetos greenfield, a skill conduz personalização em diálogo curto, fazendo perguntas específicas sobre identidade do projeto, stack, restrições não-negociáveis e foco inicial. Em alguns minutos você tem o `AGENT.md` e o `STATE.md` personalizados, prontos para o primeiro commit.

Para projetos legacy, a skill conduz gênese retroativa em quatro fases sequenciais com revisão humana entre cada uma: AGENT.md a partir do código existente, ADRs candidatos a partir do git log, Manifest a partir dos entrypoints públicos, e STATE.md inicial com auditoria. Cada fase apresenta drafts para sua aprovação antes de gravar.

## Comportamento com arquivos pré-existentes

Quando o `AGENT.md` ou o `CLAUDE.md` já existem na raiz do projeto, o `deploy.py` não os sobrescreve. Em vez disso, ele preserva o conteúdo existente e registra os arquivos em uma fila de merge pendente (`.agent-memory/.merge-queue`), salvando uma cópia do template novo para referência (`.agent-memory/.pending-merge/<arquivo>.new`). A skill `memory-deploy` então mescla o conteúdo existente com o template novo, preservando customizações do usuário e adicionando apenas estrutura faltante.

O `STATE.md` segue semântica diferente: como o conteúdo dele é volátil por construção, não há valor real em mesclar. Se já existe, é simplesmente pulado. As skills em `skills/` também são puladas se já existem.

A flag `--force` sobrescreve tudo sem merge, útil quando você quer descartar customizações e voltar aos templates limpos. A flag `--no-merge` pula arquivos existentes sem sobrescrever nem mesclar, restaurando o comportamento de "skip se existe", útil em CI onde a personalização não se aplica.

## Versionamento e atualizações

O pacote tem versionamento semântico em `VERSION` e changelog em `CHANGELOG.md`. Cada release publicada no GitHub corresponde a uma tag `vX.Y.Z` e a uma seção do `CHANGELOG.md`. Quando você instala em um projeto, a versão é registrada em `.agent-memory/.installed-version` (não versionado no Git), permitindo saber qual versão está em uso e gerenciar atualizações.

Para receber atualizações, configure uma única vez o arquivo `.agent-memory/.upstream` apontando para o repositório oficial. **Esse arquivo não é do Git** — é um arquivo de configuração lido apenas pelo `update.py`, que escolhe entre seguir uma tag ou rastrear uma branch. Veja `.upstream.example` para os formatos suportados.

```bash
# Opção A: rastrear a branch principal (sempre baixa o último commit de main)
echo "git+https://github.com/brunoleos/agent-memory.git" > .agent-memory/.upstream

# Opção B (recomendada): fixar em uma tag específica
echo "git+https://github.com/brunoleos/agent-memory.git#v0.1.0" > .agent-memory/.upstream

# Opção C: apontar para uma cópia local (durante desenvolvimento da metodologia)
echo "local:/home/usuario/agent-memory" > .agent-memory/.upstream
```

A diferença entre A e B importa: com a opção A, qualquer commit em `main` aparece como atualização disponível, mesmo que ainda não tenha virado release; com a opção B, você só vê uma atualização quando bumpar manualmente a tag no `.upstream` para a próxima release publicada. Em projetos de produção, fixar em tag dá controle; em projetos de experimentação, seguir a `main` é prático.

Com o upstream configurado, o ciclo de update tem duas chamadas:

```bash
# Verifica se há atualização disponível, sem aplicar
python .agent-memory/update.py --check

# Aplica a atualização
python .agent-memory/update.py
```

O `update.py` clona o upstream em uma pasta temporária, lê o `VERSION` de lá, e — se for diferente do `.installed-version` local — substitui o conteúdo de `.agent-memory/` preservando os arquivos de configuração específicos do clone (`.installed-version`, `.upstream`, fila de merge pendente em `.merge-queue` e `.pending-merge/`). Em seguida, re-roda o `deploy.py` com a lógica de merge para propagar mudanças aos artefatos do projeto sem perder customizações do `AGENT.md` ou do `CLAUDE.md`. A pasta temporária é removida ao final.

Para subir de uma tag fixada para a seguinte, edite o `.upstream` trocando `#v0.1.0` por `#v0.2.0` (ou a tag desejada) e rode `update.py` novamente.

## Lançamento de novas versões (mantenedor)

Esta seção é para quem mantém o `agent-memory` em si, não para quem apenas o consome. Ignore se você é apenas usuário.

Cada release segue um ciclo curto e repetível:

1. Faça as mudanças no código e em `CHANGELOG.md` (uma nova seção `## [X.Y.Z]` com a data e o que mudou).
2. Atualize o arquivo `VERSION` para `X.Y.Z`, seguindo SemVer: `patch` para correções, `minor` para adições retrocompatíveis, `major` para mudanças que quebram compatibilidade.
3. Commite tudo junto: `git commit -m "Release vX.Y.Z"`.
4. Crie a tag: `git tag vX.Y.Z`.
5. Faça o push do branch e da tag: `git push && git push --tags`.
6. Publique a release no GitHub: <https://github.com/brunoleos/agent-memory/releases/new>, selecione a tag, use como título `vX.Y.Z` (ou `vX.Y.Z - <descritivo>` em releases marcantes), e cole no corpo a seção correspondente do `CHANGELOG.md`. Marque "Set as the latest release".

A release no GitHub não muda o que o `update.py` baixa (ele opera sobre tags Git diretamente), mas serve como ponto de download formal e como histórico legível para humanos.

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
