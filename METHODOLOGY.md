# Metodologia: memória persistente para agentes

## Princípios

O problema que esta metodologia resolve é específico e mensurável: agentes LLM operando em código carregam três tipos qualitativamente distintos de conhecimento — invariantes do projeto, capacidades implementadas, foco operacional — e cada um tem ciclo de vida próprio. Misturar esses tipos em um único arquivo gera dois problemas simétricos: o conteúdo estável fica poluído por contexto efêmero, e o conteúdo efêmero compete por atenção com regras permanentes. A solução é separar por ciclo de mutação, não por tópico.

A escolha de quatro artefatos não é arbitrária. Cada um responde uma pergunta que os outros não respondem bem, e cada um tem uma regra de mutação que torna a manutenção previsível. Esta assimetria é o que mantém o sistema barato no longo prazo, mesmo após anos de desenvolvimento contínuo.

| Artefato | Pergunta | Verdade | Mutação |
|---|---|---|---|
| `AGENTS.md` | Sob quais regras? | Normativa | Rara |
| `.agent-memory/manifest/` | O que existe hoje? | Descritiva | Append-only |
| `.agent-memory/STATE.md` | Onde estamos agora? | Volátil | Reescrita bounded |
| `.agent-memory/decisions/` | Por que escolhemos assim? | Histórica | Imutável + supersede |

A metodologia adota convenções consolidadas em vez de inventar vocabulário. O arquivo `AGENTS.md` segue a convenção multi-agente reconhecida por ferramentas como Claude Code, Cursor, Aider e Continue; ADRs em pasta `decisions/` seguem o padrão de Michael Nygard de 2011; os critérios de aceitação seguem a notação EARS (Easy Approach to Requirements Syntax) com seus cinco padrões canônicos. Toda a inteligência mora na disciplina das mutações, não em ferramentas exclusivas.

## 1. Constitution: `AGENTS.md`

O `AGENTS.md` é o ponto de entrada do projeto. Ele segue a convenção multi-agente que funciona com Claude Code, Cursor, Aider, Continue e outras ferramentas, eliminando a necessidade de uma "skill de bootstrap" customizada e de duplicar instruções por ferramenta. Um arquivo `CLAUDE.md` mínimo coexiste na raiz contendo apenas `@AGENTS.md`, que faz o Claude Code carregar a constituição via sintaxe de importação. Times que usam apenas uma ferramenta podem manter só o arquivo correspondente; times multi-agente compartilham a mesma constituição sem duplicação.

O `AGENTS.md` contém apenas o que não muda entre sessões: identidade do projeto, restrições técnicas, e ponteiros para os outros artefatos.

O frontmatter YAML torna o conteúdo parseável por scripts sem sacrificar legibilidade humana. As restrições têm `severity` explícita: `hard` bloqueia o build quando violada, `soft` apenas gera warning. Esta distinção é o que separa convenções de estilo (que podem ser ignoradas em casos extremos) de regras de segurança (que nunca podem).

Cada restrição pode declarar um bloco `check` opcional que a torna **enforced** em vez de só declarativa: o `agent-memory audit` o executa contra o repositório e emite uma violação herdando a `severity` da restrição. O conjunto de checkers é fechado e genérico — `forbid_paths`, `require_paths`, `forbid_pattern`, `require_pattern` e `dependencies` — composto via YAML, sem código por regra ([ADR-0028](.agent-memory/decisions/0028-constraints-declarative-checkers.md)). Restrição sem `check` permanece puramente declarativa. Nem toda regra é mecanizável de forma barata e confiável (o idioma da documentação, por exemplo); o schema não finge que é — enforça onde dá, declara onde não dá. Tudo opera com a dependência única do projeto, sem ferramentas externas.

O campo `budgets` define os orçamentos de tamanho que o sistema impõe sobre si mesmo. O orçamento de retomada (CLAUDE + STATE + dois índices) deve ficar abaixo de doze kilobytes para que um agente possa carregar todo o contexto inicial em poucos tokens. O orçamento do State é mais agressivo, quatro kilobytes, porque o State é reescrito a cada sessão e crescimento descontrolado significa que o agente não está consolidando direito.

Mudanças em `AGENTS.md` exigem ADR sempre que alteram restrições `hard` ou referenciam novas convenções arquiteturais. A regra prática é: se a mudança requer explicação para um futuro contribuidor, ela merece ADR.

## 2. Manifest: `.agent-memory/manifest/`

O Manifest é descritivo, não aspiracional. Cada arquivo descreve uma capacidade que existe ou está sendo construída agora, com contratos verificáveis no código. A estrutura é uma pasta com um arquivo por feature mais um índice gerado automaticamente, simétrica à pasta `.agent-memory/decisions/`.

A escolha de um arquivo por feature, em vez de um arquivo monolítico, resolve três problemas simultaneamente. Diffs no Git ficam limpos quando uma feature evolui isoladamente. O agente carrega apenas as features relevantes para a tarefa atual, mantendo o orçamento de contexto sob controle. E a história de cada feature fica preservada no `git log` do seu próprio arquivo, sem precisar de timestamps redundantes no documento.

### Schema da feature

Cada arquivo de feature tem o nome `F-NNNN-slug.md`, onde NNNN é um número monotônico de quatro dígitos e slug é um identificador curto em kebab-case. O ID nunca é reutilizado; uma feature deprecada vira `status: deprecated` mas mantém o arquivo, permitindo que ADRs e outras features continuem referenciando-a com integridade.

Os campos obrigatórios do frontmatter são `id`, `name`, `status`, `user_value`, `contracts` e `acceptance`. Os opcionais incluem `version` (semver da última release que tocou a feature), `owner` (time ou pessoa), `depends_on` (lista de IDs de outras features), `decisions` (lista de IDs de ADRs relacionados) e `metrics` (medidas operacionais, com timestamp).

O campo `status` aceita quatro valores: `planned` (especificada mas não construída), `in_progress` (em construção ativa), `shipped` (entregue e em uso) e `deprecated` (mantida apenas para compatibilidade reversa). A transição de status é registrada no commit que faz a mudança.

O campo `contracts` é o mais importante porque torna o arquivo automaticamente verificável. Cada caminho referenciado deve apontar para um arquivo que existe no código (`src/api/search.py::search_endpoint` significa "função `search_endpoint` no módulo `src/api/search.py`"). O `agent-memory audit` checa estes caminhos e marca como drift qualquer referência quebrada.

### Critérios de aceitação em notação EARS

O campo `acceptance` é uma lista de critérios estruturados na notação EARS. Cada critério tem um `id` estável e um `pattern` que determina os campos obrigatórios. A notação distingue cinco situações qualitativamente diferentes em que um requisito pode se aplicar, e a explicitação do padrão elimina ambiguidade sobre quando o requisito está em vigor.

O padrão **ubiquitous** descreve um comportamento sempre ativo, uma invariante do sistema. Tem apenas o campo `requirement`. A formulação canônica é "o sistema deve sempre X". Use para propriedades que devem valer em qualquer estado, como "embeddings devem permanecer L2-normalizados".

O padrão **event** descreve uma resposta a um gatilho externo, do tipo estímulo-resposta. Tem campos `trigger` e `response`. A formulação canônica é "quando X, o sistema deve Y". Use para ações iniciadas externamente, como "quando o endpoint recebe uma query, retornar top-k".

O padrão **state** descreve um comportamento que se aplica enquanto o sistema está em determinada condição. Tem campos `state` e `response`. A formulação canônica é "enquanto X, o sistema deve Y". Use para comportamentos condicionais ao estado interno, como "enquanto reindex está rodando, retornar 503".

O padrão **optional** descreve um comportamento que se ativa quando uma feature opcional está presente. Tem campos `feature` e `response`. A formulação canônica é "onde X for fornecido, o sistema deve Y". Use para flags ou parâmetros opcionais, como "onde metric=dot_product for fornecido, usar dot product".

O padrão **unwanted** descreve uma resposta a uma situação indesejada. Tem campos `trigger` e `response`. A formulação canônica é "se X, então o sistema deve Y". Use para condições de erro e proteções defensivas, como "se um vetor zero for fornecido, retornar 400".

O padrão **complex** existe como escape para combinações que não cabem nos cinco padrões básicos. Tem apenas o campo `requirement` em prosa estruturada. Use com parcimônia: a maioria dos critérios cabe em um dos cinco padrões canônicos, e quebrar em múltiplos critérios é geralmente preferível a usar `complex`.

A validação no `agent-memory audit` exige que cada critério tenha `pattern` declarado e que os campos obrigatórios para aquele padrão estejam presentes e não-vazios. Critérios mal-formados bloqueiam o build, garantindo que a notação seja seguida consistentemente.

### Quando criar uma feature

A unidade de uma feature é uma capacidade coerente que entrega valor identificável ao usuário ou ao operador do sistema. "Pool de conexões com Oracle" é uma feature; "função que parseia JSON" não é, é detalhe de implementação. A regra prática: se você consegue escrever um `user_value` em uma frase sem usar termos puramente técnicos, é feature; senão, é parte de uma feature maior.

Features podem (e frequentemente devem) depender umas das outras. `F-0007 vector-similarity-search` depende de `F-0003 docling-ingest` e `F-0005 embedding-pipeline`, e essa cadeia fica explícita em `depends_on`. Quando uma feature é deprecada, o `agent-memory audit` detecta automaticamente outras features que ainda dependem dela e gera warning.

## 3. State: `.agent-memory/STATE.md`

O State é o único artefato verdadeiramente volátil. Ele tem orçamento de tamanho rígido (4KB) e estrutura fixa em três zonas: `Current` (estado agora, reescrito a cada sessão), `Next` (próxima ação concreta, também reescrita) e `Recent` (buffer circular de cinco linhas com SITREPs anteriores).

O orçamento não é cosmético — ultrapassá-lo é o sinal mais confiável de que o agente está acumulando contexto efêmero em vez de promovê-lo para os artefatos apropriados. Quando o State começa a inchar, as opções são duas: ou alguma decisão deveria ter virado ADR, ou alguma mudança de comportamento deveria ter virado entrada no Manifest.

O campo `active_features` no frontmatter lista os IDs das features sendo tocadas na sessão atual. Isso transforma o State em um cursor sobre o Manifest: o agente carrega apenas os arquivos de feature listados aqui, mantendo o contexto enxuto. O mesmo se aplica a `active_decisions`.

A coluna `features touched` em `Recent` cria rastreabilidade reversa sem custo adicional. Dado um problema descoberto em produção, `git log .agent-memory/STATE.md | grep F-0007` produz a linha do tempo exata de quando essa feature foi tocada e por qual agente. Esta é a métrica de observabilidade mais barata do sistema.

## 4. Decisions: `.agent-memory/decisions/`

Cada decisão arquitetural não-trivial vira um arquivo numerado em `.agent-memory/decisions/NNNN-slug.md`. Decisões nunca são editadas após `accepted`; são substituídas por novas que apontam para as antigas via `supersedes`. Esta imutabilidade é fundamental — uma decisão editável é só uma anotação, não tem o peso histórico que justifica o esforço de escrevê-la.

O frontmatter referencia features explicitamente via `affects_features`. Uma decisão pode afetar várias features, e uma feature pode encarnar várias decisões. Esta relação muitos-para-muitos é o que torna ADRs e Manifest ortogonais em vez de redundantes.

Os campos obrigatórios do frontmatter de um ADR são `id`, `date` e `status`. O campo `version` é **opcional**: quando presente, registra a release (semver `X.Y.Z`, prefixo `v` aceito) em que a decisão foi aceita — simétrico ao `version` das features. O `agent-memory audit` valida o formato quando o campo existe, mas nunca o exige (ADRs sem `version` permanecem válidos). O `agent-memory propose-adr` pré-preenche o campo com a versão atual do pacote no draft gerado. Não há backfill obrigatório: ADRs antigos sem o campo continuam corretos.

O corpo segue quatro seções padronizadas: Contexto (o problema), Decisão (a escolha feita), Consequências (positivas e negativas), Alternativas rejeitadas (com a razão da rejeição). A seção de alternativas é a mais importante e a mais frequentemente esquecida. Sem ela, um futuro leitor não tem como saber se a alternativa óbvia já foi considerada e descartada por uma boa razão, ou se ninguém pensou nela.

Quando uma decisão é substituída, o ADR original tem apenas seu campo `superseded_by` atualizado — nada mais é alterado. O ADR substituto explica o motivo da mudança em sua seção de Contexto. Esta convenção preserva o raciocínio original mesmo quando as conclusões mudam.

### Propostas de ADR (`.agent-memory/decisions/proposals/`)

Drafts gerados pela ferramenta `agent-memory propose-adr` ficam em uma subpasta separada que o `agent-memory audit` ignora explicitamente. Drafts não são ADRs e não têm validade arquitetural — são pontos de partida para conversa. Quando um draft é revisado e aprovado, o arquivo é renomeado com slug definitivo e movido para `.agent-memory/decisions/`, momento em que passa a ser auditado normalmente.

A separação é deliberada: ADRs são imutáveis e proposals são mutáveis, e misturar os dois quebraria a invariante de imutabilidade. Drafts podem (e devem) ser editados livremente até o momento da promoção; uma vez em `.agent-memory/decisions/`, ficam congelados.

## Skills

A metodologia inclui quatro skills em `skills/` na raiz do workspace (deployadas pelo `agent-memory deploy` a partir do package data em `src/agent_memory/data/skills/`) que orientam o agente nos fluxos críticos. Elas são opcionais — todo o protocolo está documentado neste arquivo — mas sua presença torna a aplicação consistente e libera o agente de precisar relembrar a doutrina inteira a cada interação.

A skill `memory-deploy` cobre a adoção inicial. Ela é o ponto de entrada único para instalar a metodologia em qualquer projeto, ativando quando o usuário pede para configurar ou adotar a estrutura. A skill detecta automaticamente se o projeto é greenfield (poucos commits, pouco código, sem entrypoints públicos) ou legacy (histórico substancial, código de produção, stack identificável), e ramifica para o fluxo apropriado. Em ambos os casos, ela executa o `agent-memory deploy` para a estrutura mecânica antes de personalizar — o comando é a infraestrutura subjacente que a skill orquestra. Para greenfield, segue personalização interativa em diálogo curto sobre identidade, stack, restrições e foco inicial. Para legacy, segue gênese retroativa em quatro fases revisadas (constituição a partir do código, ADRs a partir do git log, Manifest a partir dos entrypoints, STATE inicial), com o princípio fundamental de que cristalização silenciosa de interpretações erradas é o pior erro possível.

A skill `memory-bootstrap` cobre o início de sessão. Ela ativa quando o usuário pergunta sobre o estado atual do projeto e instrui o agente a carregar `.agent-memory/STATE.md` e os índices, expandir apenas features e ADRs ativos, e apresentar um briefing tático curto antes de prosseguir. Quando detecta que o último commit é um merge que tocou artefatos da metodologia, ela delega para `memory-pull-brief` antes do briefing tático.

A skill `memory-debrief` cobre o fim de unidade de trabalho. Ela ativa quando o usuário sinaliza intenção de commitar e instrui o agente a examinar o diff, atualizar entradas do Manifest para features tocadas, reescrever as zonas `Current` e `Next` do `.agent-memory/STATE.md`, e gerar proposta de ADR via `agent-memory propose-adr` se a sessão produziu uma decisão arquitetural não-trivial. Esta é a skill mais usada no dia-a-dia, porque cobre o momento em que o trabalho realizado precisa ser refletido na memória persistente antes de virar commit.

A skill `memory-pull-brief` cobre o momento pós-`git pull` em projeto cliente que recebeu commits de colegas. Ela ativa por trigger manual ("o que veio do pull", "brifa as mudanças do main") ou por delegação a partir da `memory-bootstrap`. Examina o diff trazido pelo pull, identifica mudanças semânticas em features e ADRs (transições de status, novos IDs, supersedes), cruza com `STATE.md::active_features` e `active_decisions` do desenvolvedor local, e propõe ajustes em `.agent-memory/STATE.md` para refletir a nova realidade. Por design é read-only sobre `.agent-memory/manifest/` e `.agent-memory/decisions/` — esses já vieram corretos do pull, e escrever neles seria reverter trabalho de colegas.

A separação em quatro skills em vez de uma reflete a estrutura real do trabalho com a metodologia: quatro momentos qualitativamente diferentes (adoção, início de sessão, fim de unidade, sincronização pós-pull), cada um com sua própria checklist e cada um com seus próprios riscos de ser executado errado. Skills monolíticas tendem a ser ignoradas; skills específicas e curtas tendem a ser invocadas no momento certo.

A escolha de fazer da `memory-deploy` o ponto de entrada — em vez de exigir que o usuário invoque o `agent-memory deploy` diretamente — reflete uma decisão de design importante. O comando sozinho instala a estrutura mecânica mas não personaliza nada, o que deixa um projeto greenfield com `AGENTS.md` genérico inútil ou um projeto legacy com Manifest vazio que ignora todo o código existente. A skill envolve o comando com a inteligência necessária para que a instalação produza valor real desde o primeiro commit. O comando direto permanece disponível para automação e CI, onde personalização não se aplica.

## Workflow de merge e rebase

Os quatro artefatos têm comportamentos qualitativamente diferentes sob merge, e tratá-los uniformemente produz resultados ruins. A metodologia adota estratégias diferenciadas suportadas por configuração Git e por convenções de workflow que as skills já promovem implicitamente.

O `.agent-memory/STATE.md` é o caso patológico clássico. Duas branches paralelas reescrevem `Current` e `Next` para refletir focos diferentes, e o merge produz conflito em praticamente todo commit colaborativo. A configuração `merge=ours` no `.gitattributes` resolve automaticamente, mantendo a versão da branch destino. O `.agent-memory/STATE.md` não é fonte de verdade compartilhada — é o cursor da última sessão de trabalho ativa, e tentar mesclar duas visões paralelas produz texto incoerente sem ganho operacional.

Os índices gerados (`.agent-memory/manifest/INDEX.md` e `.agent-memory/decisions/INDEX.md`) seguem a mesma estratégia. Eles são recriados a cada execução do `agent-memory audit`, então a regra prática é resolver o conflito escolhendo qualquer versão e regenerar. A configuração `merge=ours` para esses dois arquivos elimina o conflito explicitamente, e a skill `memory-bootstrap` detecta sessões pós-merge para regenerar automaticamente.

Os ADRs em `.agent-memory/decisions/` enfrentam um problema diferente: colisão de IDs quando branches paralelas criam ADRs simultaneamente. O Git em si não detecta isso como conflito (são arquivos diferentes), mas o resultado é semanticamente quebrado. A solução é renumerar o ADR mais recente após o merge, ajustando todas as referências cruzadas. O `agent-memory audit --check-collisions origin/main` detecta a situação preventivamente quando rodado na branch antes do merge, e a skill `memory-debrief` invoca essa checagem na rotina pré-commit em branches que serão mescladas.

As features em `.agent-memory/manifest/features/` têm dois sub-casos. Quando duas branches criam features novas com IDs diferentes, não há conflito real e o merge é trivial. Quando duas branches modificam a mesma feature existente (por exemplo, ambas adicionando critérios de aceitação ou atualizando métricas), há conflito real que precisa de resolução manual. A estratégia recomendada é mesclar à mão, preservando todas as adições de ambos os lados (critérios de aceitação são aditivos por natureza), e tomando a versão mais recente para campos como `metrics` ou `version` que têm semântica de substituição. Colisão de IDs em features é detectada pelo mesmo `--check-collisions` que cobre ADRs.

Para rebase, a dinâmica é a mesma com uma sutileza. O rebase replica os commits da feature branch sobre a branch destino atualizada, então conflitos de ADR ou State aparecem em cada commit replicado. A configuração `merge=ours` cobre State e índices. Para ADRs com colisão de ID, o ideal é resolver a colisão antes do rebase (renumerando na feature branch enquanto ela ainda é local), em vez de durante o rebase quando o contexto está mais opaco. Isso reforça a importância da checagem `--check-collisions` na rotina de debrief.

A configuração do driver `merge.ours.driver` no Git é feita automaticamente pelo `agent-memory deploy`, que executa `git config merge.ours.driver true` no projeto. Em outros clones do mesmo repositório, cada desenvolvedor precisa rodar essa configuração manualmente uma vez (o `agent-memory deploy` faz isso, mas o `.gitattributes` já versionado pode não disparar nova execução do deploy). A documentação do `.gitattributes` deployado registra a instrução para esses casos.

## Protocolo do agente

O protocolo cabe em três frases e opera sobre os quatro artefatos sem precisar de skill customizada — agentes que reconhecem `AGENTS.md` (Claude Code via redirect, Cursor, Aider, Continue) já carregam a constituição automaticamente.

Na inicialização, o agente carrega `AGENTS.md`, `.agent-memory/STATE.md`, `.agent-memory/manifest/INDEX.md` e `.agent-memory/decisions/INDEX.md`. O total fica dentro do orçamento de doze kilobytes definido em `AGENTS.md::budgets::resumption_max_bytes`. O agente então expande apenas as features listadas em `STATE.md::active_features` e os ADRs em `STATE.md::active_decisions`.

Durante o trabalho, qualquer mudança de comportamento exige atualizar a feature correspondente no Manifest no mesmo commit do código. O Manifest é a única fonte de verdade sobre o que o sistema faz; se uma capacidade não está no Manifest, ela não existe, mesmo que o código já tenha sido escrito. Esta rigidez parece custosa mas paga dividendos imediatos: o problema clássico de agentes inventando features que não combinam com o sistema existente desaparece.

No debrief, o agente reescreve as seções `Current` e `Next` do `.agent-memory/STATE.md`, adiciona uma linha em `Recent`, atualiza ou cria entradas no Manifest para features tocadas, e cria um ADR se a sessão produziu uma decisão arquitetural não-trivial. O debrief é parte do trabalho, não opcional — uma sessão sem debrief é trabalho perdido.

## Auditoria

O `agent-memory audit` produz um relatório de uma página com oito indicadores. Cada um responde uma pergunta operacional concreta sobre se o sistema está entregando valor ou virando burocracia.

A **conformidade de schema** mede se todos os artefatos passam validação estrutural, incluindo a validação dos critérios de aceitação contra os padrões EARS. Qualquer erro aqui bloqueia o build — schemas inválidos significam que o agente vai consumir dados quebrados na próxima sessão.

A **conformidade de constraints** mede as restrições `hard`/`soft` que declaram um bloco `check`: o audit executa cada checker contra o repositório e reporta quantas foram checadas e quantas violaram. Violação de restrição `hard` é error e bloqueia o build; `soft` é warning. Restrições sem `check` não entram na conta. É o indicador que torna a constituição enforced em vez de só lida (ADR-0028).

O **custo de retomada** soma os bytes de `AGENTS.md`, `CLAUDE.md` (quando presente como redirect), `.agent-memory/STATE.md` e os dois índices. Acima de doze kilobytes, o sistema está consumindo tokens demais antes mesmo do trabalho começar; é hora de compactar índices ou consolidar State.

O **frescor de estado** mede o tempo desde o último update do `.agent-memory/STATE.md`. Acima de uma semana, a última sessão não fez debriefing — bug de processo, não de software.

A **cobertura do manifest** mede a porcentagem de features cujo campo `contracts.tests` aponta para arquivos de teste que existem. Cobertura caindo significa que estamos enviando capacidades sem rede de segurança.

O **drift do manifest** lista features cujos contratos apontam para caminhos inexistentes. Drift não-vazio significa que código foi refatorado sem atualizar o Manifest — viola a regra fundamental de "Manifest e código commitados juntos".

A **velocity** detecta a patologia mais comum: features que entram em `in_progress` e nunca saem. Acima de catorze dias em progresso é warning; acima de trinta é problema operacional.

A **saúde de decisões** mede a razão de substituição (superseded sobre total) e o número de decisões em `accepted` há mais de cento e oitenta dias sem revisão. Razão muito baixa significa decisões fossilizadas; muito alta, decisões tomadas sem maturidade. A faixa saudável fica entre vinte e cinquenta por cento.

### Modo strict

A flag `--strict` promove warnings (drift) a errors. Em modo padrão o `agent-memory audit` retorna exit 0 mesmo com drift presente, porque drift pode ser temporário (você refatorou e ainda vai atualizar o Manifest no próximo commit). Em modo strict, qualquer drift bloqueia. O modo strict é usado pelo pre-commit hook e deve ser usado pela CI.

## Pre-commit hook

O hook em `src/agent_memory/governance/data/hooks/pre-commit` é instalado em `.git/hooks/pre-commit` automaticamente pelo `agent-memory deploy`. Como o diretório `.git/` não é versionado, cada clone do projeto consumidor precisa rodar `agent-memory deploy` uma vez para instalar o hook.

O hook roda `agent-memory audit --strict --no-index` antes de cada commit. Se a auditoria falha — schema inválido, EARS mal-formado, drift detectado — o commit é bloqueado e o desenvolvedor vê a lista exata de problemas. Para contornar deliberadamente em situações excepcionais, `git commit --no-verify` ignora todos os hooks. Esta válvula de escape é importante: hooks que não podem ser ignorados acabam sendo desinstalados, e o objetivo é nudge, não coerção.

A combinação hook local mais checagem em CI é o padrão recomendado. O hook pega a maioria dos problemas no início do ciclo de feedback, quando o custo de correção é mínimo; a CI pega os casos onde o hook foi pulado ou não estava instalado, e impede merges incorretos. Sem hook local, todo erro espera o tempo de CI para ser detectado.

## Geração de propostas de ADR

A ferramenta `agent-memory propose-adr` examina o diff atual contra um commit base (HEAD~1 por padrão, ou mudanças staged com `--staged`) e aplica heurísticas para detectar mudanças que podem merecer um ADR. Os sinais que ela observa incluem volume da mudança (cinco arquivos ou cem linhas), alterações em arquivos de manifesto de dependências, mudanças em três ou mais diretórios distintos, e mensagens de commit contendo padrões linguísticos de decisão como "switched from", "instead of", "deprecated".

Quando os sinais são detectados, a ferramenta gera um draft pré-preenchido em `.agent-memory/decisions/proposals/NNNN-draft.md`, com as seções TODO marcadas e os sinais detectados anotados como contexto. O draft não é um ADR — é matéria-prima para um, e o `agent-memory audit` ignora a subpasta `proposals/` para preservar a invariante de que ADRs verdadeiros são imutáveis.

A ferramenta também oferece um modo `--prompt` que emite um prompt estruturado para um agente LLM em vez de gerar o template diretamente. Este modo é útil quando você quer aproveitar a presença de um agente Claude para redigir o draft completo, e o prompt já inclui as instruções para o agente decidir se a mudança realmente merece um ADR (recusando explicitamente se for trivial) e para preencher cada seção com substância em vez de placeholders.

A separação entre detecção e redação é deliberada. A detecção é determinística e barata; a redação exige julgamento. Manter as duas etapas separadas evita que o sistema gere automaticamente ADRs vazios apenas porque algumas heurísticas dispararam, o que poluiria a memória arquitetural com ruído.

## Migração

Para um projeto novo, criar `AGENTS.md`, `.agent-memory/STATE.md`, `.agent-memory/manifest/` e `.agent-memory/decisions/` leva minutos, e a primeira feature a ser entregue já segue o protocolo. Para projetos legados, a migração tem dois passos sequenciais.

Primeiro, `agent-memory migrate` examina os últimos cem ou duzentos commits e propõe ADRs candidatos a partir de mensagens contendo padrões como "switched", "instead of", "revert", "decided to". Os candidatos são impressos para revisão humana, não escritos automaticamente. Esta restrição é deliberada — gênese retroativa não pode ser silenciosa, sob pena de cristalizar interpretações erradas como decisões oficiais.

Segundo, o agente examina os módulos públicos do código (entrypoints da API, casos de uso, comandos CLI) e propõe entradas iniciais do Manifest, marcando-as como `status: shipped` mas sem métricas. O humano revisa e aprova antes da gravação. Em sistemas grandes (cento e oitenta mil linhas, mais de um ano de desenvolvimento), o agente trabalha como assistente da migração, não como executor autônomo: ele propõe, o humano dispõe.

## Casos de borda

**E quando duas sessões paralelas tocam o State?** A versão atual assume sessão única em série. Para múltiplos agentes simultâneos, ver `FUTURE_IMPROVEMENTS.md` (item de coordenação multi-agente). A heurística atual é que `.agent-memory/STATE.md` é append-only estrito em `Recent` com IDs monotônicos por SITREP, e `Current` e `Next` ficam sob lock pessimista do Git (último commit ganha, e o conflito é visível).

**E features muito pequenas?** Se uma capacidade não merece um arquivo próprio, provavelmente é parte de uma feature maior. Resista à tentação de criar features triviais — o Manifest perde valor quando vira lista de funções. A regra é a mesma do início: `user_value` em uma frase sem termos puramente técnicos.

**E ADRs para mudanças menores?** Se a mudança não exigiria explicação para um futuro contribuidor, ela não merece ADR. A pergunta operacional: "se eu olhar este commit em seis meses, vou entender por que essa escolha?" Se a resposta for sim, comentário no commit basta; se for não, vire ADR. A ferramenta `agent-memory propose-adr` ajuda a calibrar essa intuição, mas a decisão final é humana.

**E quando o `agent-memory audit` reporta drift mas o caminho está certo?** Verifique convenções de path: o `agent-memory audit` checa caminhos relativos à raiz do projeto. `src/api/search.py::search_endpoint` é interpretado como "arquivo `src/api/search.py` existe", o `::search_endpoint` é metadata para o agente. Drift vem de arquivos movidos ou renomeados sem atualizar o Manifest.

**E para projetos sem testes?** Cobertura zero é cobertura honesta. Melhor que cobertura inflada por testes inexistentes. Se a equipe não tem prática de testes, o Manifest expõe esse débito explicitamente, o que é o primeiro passo para resolvê-lo.

**E se o pre-commit hook está bloqueando trabalho legítimo?** A flag `--no-verify` no `git commit` ignora todos os hooks. Use com critério: se você está usando regularmente, o sinal é que ou o hook está calibrado errado (drift transitório sendo bloqueado) ou o time precisa de treinamento na metodologia. Investigue a causa em vez de tornar `--no-verify` rotina.
