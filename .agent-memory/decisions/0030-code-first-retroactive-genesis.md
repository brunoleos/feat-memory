---
id: ADR-0030
date: 2026-06-03
status: accepted
version: 0.13.0
supersedes: null
superseded_by: null
affects_features: [F-0026]
related: [ADR-0004, ADR-0009]
tags: [methodology, genesis, legacy, migrate, skill, manifest]
---

# ADR-0030 · gênese retroativa é code-first; git log é fonte secundária

## Contexto

A skill `memory-deploy` conduzia a gênese retroativa (Etapa 3) na ordem: **Fase 3.1
ADRs a partir do git log**, depois **Fase 3.2 Manifest a partir dos entrypoints**.
O comando `agent-memory migrate` reforçava isso: seu output liderava com os
"candidatos a ADR" extraídos de mensagens de commit, e seu `detect_entry_points`
só varria globs `*.py`.

Dois problemas observados na adoção em `tensegrams`:

1. **Git-log-centrismo.** Num repo com histórico squashado (3 commits, o primeiro um
   squash gigante), o git log rende quase nada — e a skill levava o agente a começar
   por ele. A fonte mais rica de verdade, o **código que está lá**, ficava em segundo
   plano. Decisões de projeto (uma camada de adapters, uma dep que substituiu outra,
   um hard cut de formato) são visíveis na estrutura do código muito antes de
   aparecerem — se é que aparecem — no git log.

2. **Cegueira a linguagem.** `detect_entry_points` com globs `*.py` retornava
   **vazio** para a `tensegrams` (JS, ~80 arquivos em `src/`). O agente externo teve
   que sair globando `src/**/*.js` na mão. A ferramenta que deveria apontar onde
   olhar não apontava nada fora de Python.

O feedback do mantenedor cristalizou o princípio: *"o git log deve ser apenas uma
das fontes; a maior análise do agente deve ser sobre o próprio código do cliente —
extrair features e decisões pelo que ele vê no código."*

## Decisão

A gênese retroativa é **code-first**. O código do projeto é a fonte **primária**; o
git log é fonte **secundária**, que só data e justifica decisões já identificadas no
código — nunca o ponto de partida.

1. **Skill `memory-deploy`, Etapa 3 reordenada:**
   - Fase 3.1 passa a ser *"ler o código e mapear capacidades e decisões"* — o
     agente lê os entrypoints reais (não só diretórios de convenção: também
     `package.json::bin`/`exports`, `main`, `index.*`, rotas declaradas) e extrai em
     paralelo capacidades (→ features) e decisões de projeto visíveis na estrutura
     (→ ADRs).
   - Fase 3.2 vira Manifest a partir dessas capacidades.
   - Fase 3.3 vira ADRs a partir das decisões extraídas do código, **usando o git
     log como fonte secundária** para datar/justificar; quando o histórico não cobre
     (squash), data com a melhor evidência e descreve o contexto a partir do código.
   - Fase 3.4 é o STATE inicial + audit (antiga 3.3).

2. **`agent-memory migrate` agnóstico de linguagem.** `detect_entry_points` varre
   diretórios de convenção (`routes`, `api`, `handlers`, `controllers`, `cli`,
   `commands`, `use_cases`, `services`, `pages`, …) em qualquer extensão de fonte
   reconhecida (`.py .js .ts .go .rs .rb .java .kt .ex .php` e variantes), podando
   vendored/build (`node_modules`, `dist`, `.venv`, …) via `os.walk`. O output
   reordena: entrypoints (por onde começar a ler o código) **primeiro**, candidatos
   de commit **depois**, rotulados explicitamente como fonte secundária. O git log
   ausente deixa de ser tratado como problema.

3. **A ferramenta dá pistas; o agente lê o código.** O `migrate` continua sendo só
   um indicador de "por onde começar" — não um inventário. A análise real é a
   leitura do código pelo agente, conforme a skill.

## Consequências

Positivas: a gênese deixa de depender da qualidade do histórico de commits e passa a
extrair do artefato mais confiável (o código em produção); projetos não-Python e com
histórico squashado deixam de ser cidadãos de segunda classe; o Manifest e os ADRs
gerados refletem o que o sistema *é*, não só o que os commits *contam*.

Negativas: ler o código é mais caro em tokens/tempo que varrer mensagens de commit
(aceito — é onde está o valor); `detect_entry_points` por convenção de diretório
ainda erra projetos que não seguem nenhuma convenção (mitigado: a skill manda ler os
entrypoints reais da linguagem, não confiar só na varredura).

## Alternativas rejeitadas

- **Manter git-log-first e só consertar os globs:** corrige a cegueira de linguagem
  mas não o vício de origem — o agente continuaria começando pela fonte mais pobre.
- **Parser/AST por linguagem para extrair capacidades automaticamente:** pesado e
  acoplado a linguagem (mesmo anti-padrão rejeitado em ADR-0028). A leitura conduzida
  pelo agente é agnóstica e mais barata de manter.
- **Abandonar o git log na gênese:** ele agrega valor real para *datar* e *recuperar
  a justificativa* de decisões; rebaixá-lo a secundário preserva esse valor sem
  deixá-lo ditar a ordem.
