# Manual do usuário

Este manual cobre o uso prático da metodologia de memória persistente para agentes em projetos reais. A documentação técnica completa da doutrina está em `METHODOLOGY.md`; o roadmap de extensões está em `FUTURE_IMPROVEMENTS.md`. Este manual é o ponto de entrada para usuários novos.

## O que este projeto resolve

Agentes LLM perdem todo o contexto entre sessões. Sem memória persistente, você precisa explicar o projeto inteiro toda vez que abre uma nova sessão, ou aceitar que o agente vai inventar premissas, ignorar decisões já tomadas, e refazer trabalho que já foi feito. Em projetos pequenos isso é apenas tedioso; em projetos médios a grandes, vira um gargalo real que limita o quanto você consegue delegar ao agente.

A solução é uma camada de memória estruturada em quatro artefatos versionados, um para cada tipo qualitativamente diferente de conhecimento sobre o projeto. A constituição (`AGENT.md`) registra as regras invariantes que o agente deve respeitar sempre. O manifesto (`manifest/`) descreve o que o sistema faz hoje, com critérios verificáveis. O estado (`STATE.md`) registra o foco atual em até quatro kilobytes, atualizado a cada sessão. As decisões (`decisions/`) registram escolhas arquiteturais imutáveis com supersedência explícita. Três skills automatizam os fluxos mais comuns (instalação, início de sessão, debrief antes de commit), e ferramentas em Python validam consistência e detectam problemas.

## Quando usar este projeto

A metodologia faz sentido quando pelo menos duas destas condições são verdadeiras: o projeto vai durar mais de algumas semanas, várias pessoas (humanas ou agentes) vão tocar o código, há decisões arquiteturais não-triviais que merecem registro, e há valor em poder retomar trabalho rapidamente sem reler tudo. Para um script de uso único ou um experimento descartável, a metodologia é overhead injustificado.

A metodologia também faz sentido em projetos legados que estão sendo retomados após pausa longa, onde o conhecimento sobre por que certas escolhas foram feitas se perdeu. Nesse caso, a skill de gênese retroativa reconstrói parte desse conhecimento a partir do histórico Git e do código existente.

## Instalação em três comandos

A instalação completa tem três passos. Primeiro, traga a pasta `.agent-memory/` para a raiz do seu projeto a partir do repositório oficial em <https://github.com/brunoleos/agent-memory>. Segundo, abra uma sessão com seu agente preferido (Claude Code, Cursor, ou outro que reconheça `AGENT.md`) e diga "instale a metodologia neste projeto". A skill `memory-deploy` assume o controle, detecta se o projeto é greenfield ou legacy, executa o `deploy.py`, e conduz a personalização apropriada. Terceiro, faça o primeiro commit dos artefatos gerados com mensagem clara como "adopt agent memory methodology".

A maneira recomendada de fazer o passo 1 é clonar a tag mais recente da página de releases (<https://github.com/brunoleos/agent-memory/releases>) e copiar apenas a pasta `.agent-memory/` para o seu projeto:

```bash
git clone --depth 1 --branch v0.1.0 \
  https://github.com/brunoleos/agent-memory.git /tmp/agent-memory
cp -r /tmp/agent-memory/.agent-memory ./
rm -rf /tmp/agent-memory
```

Substitua `v0.1.0` pela tag corrente. Alternativamente, baixe o tarball de uma release específica via `curl` ou pelo botão "Source code (tar.gz)" na página da release no GitHub. Para automação ou CI, o script pode ser invocado diretamente com `python .agent-memory/deploy.py --no-merge`; a flag `--no-merge` evita criar fila de merge pendente em ambientes onde não há agente para processá-la, e os templates ficam genéricos sem personalização.

A única dependência externa do projeto é PyYAML, que pode ser instalado via `pip install pyyaml`. Todas as outras ferramentas usam apenas a biblioteca padrão do Python 3.10 ou superior, garantindo portabilidade entre Linux, macOS e Windows sem necessidade de WSL ou outras camadas de compatibilidade.

## Os quatro artefatos no dia-a-dia

A constituição em `AGENT.md` é o arquivo que você personaliza uma vez no início e raramente toca depois. Ela contém o nome do projeto, a stack técnica, restrições não-negociáveis com severidade explícita (`hard` bloqueia o build, `soft` apenas avisa), e ponteiros para os outros artefatos. Mudanças nesta constituição que alteram restrições `hard` exigem ADR registrando a justificativa. O Claude Code carrega `AGENT.md` automaticamente via `CLAUDE.md`, e outros agentes que reconhecem a convenção também o carregam.

O manifesto em `manifest/features/` é onde você registra cada capacidade do sistema. Cada arquivo tem o nome `F-NNNN-slug.md` (por exemplo, `F-0007-vector-similarity-search.md`) e descreve uma capacidade nomeável que entrega valor identificável. O frontmatter YAML contém metadados estruturados (status, versão, dependências, decisões relacionadas) e os critérios de aceitação seguem a notação EARS com cinco padrões canônicos. O índice em `manifest/INDEX.md` é gerado automaticamente pelo `audit.py` e nunca deve ser editado à mão.

O estado em `STATE.md` é o único artefato verdadeiramente volátil. Ele tem orçamento rígido de quatro kilobytes e estrutura fixa em três zonas: `Current` (estado agora), `Next` (próxima ação concreta), e `Recent` (buffer circular de cinco linhas com SITREPs anteriores). A skill `memory-debrief` reescreve as zonas `Current` e `Next` ao final de cada unidade de trabalho, e a skill `memory-bootstrap` lê o estado no início da próxima sessão para retomar exatamente de onde parou.

As decisões em `decisions/` são imutáveis depois de aceitas. Cada arquivo tem nome `NNNN-slug.md` (por exemplo, `0007-cosine-similarity-default.md`) e segue quatro seções padronizadas: Contexto (o problema), Decisão (a escolha feita), Consequências (positivas e negativas), Alternativas rejeitadas (com a razão da rejeição). Decisões que precisam mudar não são editadas; são substituídas por novas que apontam para as antigas via `supersedes`, preservando o raciocínio histórico mesmo quando a conclusão muda.

## Fluxo de trabalho típico

Um dia normal de trabalho com a metodologia segue um padrão simples. No início da sessão, você diz ao agente "onde paramos?" ou simplesmente entra no projeto e a skill `memory-bootstrap` carrega `STATE.md`, expande apenas as features e decisões ativas listadas em `active_features` e `active_decisions`, e apresenta um briefing tático curto de até cinco linhas. Você confirma se quer prosseguir com o `Next` registrado ou tem outra prioridade.

Durante o trabalho, o agente segue as restrições da constituição automaticamente. Se você está modificando uma feature existente, ele atualiza o arquivo correspondente em `manifest/features/` no mesmo commit do código. Se você toma uma decisão arquitetural não-trivial, ele propõe um ADR via `propose-adr.py` ou diretamente como rascunho em `decisions/proposals/`. Se a mudança quebra restrições `hard` declaradas em `AGENT.md`, o pre-commit hook bloqueia o commit antes que ele aconteça.

Antes de cada commit relevante, você diz ao agente "vou commitar" ou "atualize o STATE", e a skill `memory-debrief` executa a rotina completa: examina o diff, atualiza entradas do Manifest para features tocadas, reescreve as zonas `Current` e `Next` do `STATE.md`, gera proposta de ADR se a sessão produziu decisão arquitetural, e roda a auditoria. Se a sessão está em uma branch que será mesclada de volta, a skill também checa colisões de IDs contra a branch destino, evitando o problema antes que ele apareça no merge.

## Atualizações da metodologia

A metodologia evolui ao longo do tempo, e cada projeto que a adota precisa de um caminho claro para receber essas evoluções sem perder customizações locais. O versionamento semântico em `VERSION` e o histórico em `CHANGELOG.md` tornam a evolução transparente, e o arquivo `.agent-memory/.installed-version` registra qual versão está em uso em cada projeto consumidor (esse arquivo é gerado pelo `deploy.py` e fica fora do Git).

Para receber atualizações, configure o upstream em `.agent-memory/.upstream` com a fonte do pacote. **Esse arquivo não é do Git** — apesar do prefixo `git+`, ele é apenas um arquivo de configuração lido pelo `update.py`, que aceita três formatos: um repositório Git remoto (`git+URL`), uma referência específica desse repositório (`git+URL#tag`, `git+URL#branch` ou `git+URL#commit`), ou um caminho local para desenvolvimento da própria metodologia (`local:caminho`). O arquivo `.upstream.example` documenta os três formatos e pode ser copiado e editado.

A escolha entre seguir uma branch e fixar em uma tag importa. Quando você usa `git+https://github.com/brunoleos/agent-memory.git`, o `update.py` baixa o último commit da branch padrão; isso é prático em projetos experimentais mas pode trazer mudanças não anunciadas em release formal. Quando você usa `git+https://github.com/brunoleos/agent-memory.git#v0.1.0`, o `update.py` baixa apenas a tag indicada; para subir de versão, você edita o `.upstream` trocando a tag. Em projetos de produção, fixar em tag dá controle explícito sobre quando aceitar mudanças.

Com o upstream configurado, `python .agent-memory/update.py --check` verifica se há atualização disponível sem aplicá-la, mostrando a versão instalada e a versão upstream lado a lado. O comando `python .agent-memory/update.py` aplica a atualização: clona o upstream em diretório temporário, substitui a pasta `.agent-memory/` preservando arquivos de configuração local (`.installed-version`, `.upstream`, `.merge-queue`, `.pending-merge/`), atualiza o marcador de versão, e re-roda o `deploy.py` para propagar mudanças aos artefatos do projeto. A lógica de merge para `AGENT.md` e `CLAUDE.md` é a mesma do deploy inicial, garantindo que customizações sejam preservadas.

Para times que usam a metodologia em múltiplos projetos, a recomendação é apontar todos os projetos consumidores para o mesmo repositório upstream (no caso oficial, <https://github.com/brunoleos/agent-memory>), idealmente fixados na mesma tag. Atualizações na metodologia ficam disponíveis para todos os projetos via `update.py`, e cada projeto decide quando aplicar conforme seu próprio cronograma. Se você mantém um fork interno, basta apontar o `.upstream` para ele em vez do oficial.

## Comandos importantes

A auditoria é a ferramenta mais usada e cobre validação de schemas, geração de índices automáticos, e cálculo dos sete indicadores de saúde do projeto. A invocação básica é `python .agent-memory/tools/audit.py`, que emite um relatório legível e atualiza os índices. Para CI, use `python .agent-memory/tools/audit.py --json --strict`, que emite saída estruturada e promove warnings (drift) a errors. Para o pre-commit hook, o modo `--strict --no-index` é o padrão, validando sem regenerar arquivos durante o commit.

Para detectar colisões de IDs antes de um merge, use `python .agent-memory/tools/audit.py --check-collisions origin/main` (ou a branch destino que você usar). A checagem compara os IDs criados na branch atual com os existentes na branch destino, alertando se duas branches paralelas criaram o mesmo ID. Renumere antes de mesclar para evitar estado semanticamente quebrado.

Para gerar propostas de ADR a partir do diff atual, use `python .agent-memory/tools/propose-adr.py --staged`. A ferramenta examina o diff, detecta sinais de mudança arquitetural não-trivial (volume, dependências alteradas, mudanças em múltiplos diretórios, padrões linguísticos em mensagens de commit), e gera um draft em `decisions/proposals/`. Drafts não são ADRs verdadeiros; são pontos de partida para revisão humana antes de promover para `decisions/`.

Para projetos legacy adotando a metodologia, use `python .agent-memory/tools/migrate.py --limit 200`. A ferramenta examina os últimos commits do Git e propõe ADRs candidatos a partir de padrões linguísticos. Os candidatos são impressos para revisão humana, não escritos automaticamente. A skill `memory-deploy` invoca essa ferramenta automaticamente na fase 2 da gênese retroativa.

## Resolução de problemas comuns

Quando o pre-commit hook bloqueia um commit que parece legítimo, examine a saída da auditoria. Drift de contratos significa que `manifest/features/F-NNNN.md` aponta para arquivos de código que não existem mais, geralmente porque você refatorou sem atualizar a feature correspondente. A solução é atualizar a feature no mesmo commit do código. Se você precisa contornar deliberadamente em situação excepcional, `git commit --no-verify` ignora todos os hooks, mas use com critério: hooks que não podem ser ignorados acabam sendo desinstalados, e o hook é aliado, não inimigo.

Quando o estado em `STATE.md` parece estar inconsistente com o código real, o problema é geralmente uma sessão anterior que não fez debrief direito. A solução é invocar a skill `memory-debrief` agora, examinando o diff acumulado desde o último update e atualizando `Current` e `Next` para refletir a realidade atual. A coluna `features touched` em `Recent` ajuda a rastrear o que mudou entre updates do State.

Quando duas branches têm features ou ADRs com IDs colidentes, rode `--check-collisions` antes do merge. A solução é renumerar o artefato mais novo na branch que ainda não foi mesclada, atualizando o nome do arquivo, o campo `id` no frontmatter, e qualquer referência cruzada em outras features ou ADRs. ADRs já mesclados na branch destino nunca são renumerados.

Quando o `audit.py` reporta erros de notação EARS em critérios de aceitação, examine o `pattern` declarado e os campos obrigatórios para aquele padrão. Os cinco padrões canônicos são `ubiquitous` (sempre ativo, requer `requirement`), `event` (gatilho externo, requer `trigger` e `response`), `state` (em condição, requer `state` e `response`), `optional` (feature opcional, requer `feature` e `response`), e `unwanted` (situação indesejada, requer `trigger` e `response`). O sexto padrão `complex` existe como escape mas deve ser usado com parcimônia.

## Trabalhando em time

Quando o time tem múltiplas pessoas tocando o projeto, a metodologia funciona sem coordenação adicional na maioria dos casos. Cada pessoa abre uma branch, trabalha, faz debrief, commita, e merge. A configuração `.gitattributes` resolve automaticamente os conflitos previsíveis em `STATE.md` e nos índices, mantendo a versão da branch destino e regenerando o que precisa ser regenerado.

Os dois pontos onde coordenação importa são a escolha de IDs novos (que pode produzir colisão) e a modificação simultânea da mesma feature (que pode produzir conflito real). Para o primeiro, a skill `memory-debrief` checa colisões automaticamente e propõe renumeração. Para o segundo, a resolução é manual seguindo a regra de "preservar adições, substituir campos de overwrite": critérios de aceitação são aditivos, métricas são substitutivas.

Em projetos onde múltiplos agentes podem rodar em paralelo (por exemplo, um agente de coding mais um agente de testes mais um humano), a metodologia ainda funciona em série. A coordenação multi-agente em paralelo está documentada como melhoria futura em `FUTURE_IMPROVEMENTS.md`.

## Casos de uso de referência

A metodologia foi projetada com três casos de uso principais em mente, e a documentação inclui exemplos pedagógicos de cada um. O caso de uso de uma feature de busca semântica em banco vetorial, exemplificado por `examples/manifest/features/F-0001-vector-similarity-search.md`, mostra como uma capacidade técnica não-trivial é decomposta em metadados estruturados, contratos verificáveis, e seis critérios de aceitação cobrindo os cinco padrões EARS. O caso de uso de uma decisão sobre métrica de similaridade, exemplificado por `examples/decisions/0002-cosine-similarity-default.md`, mostra como uma escolha técnica que parece pequena vira ADR quando há trade-offs reais e alternativas rejeitadas. O caso de uso da própria adoção da metodologia, exemplificado por `examples/decisions/0001-record-architecture-decisions.md`, mostra como o ADR fundacional registra a meta-decisão de adotar ADRs.

Estes exemplos não são copiados pelo `deploy.sh` para o seu projeto, ficando apenas em `.agent-memory/examples/` para consulta. Você pode usar o ADR-0001 como ponto de partida para o seu próprio ADR fundacional adaptando o contexto, mas os outros dois exemplos são puramente pedagógicos.

## Próximos passos

Depois de instalar a metodologia, três ações curtas estabelecem a fundação. Primeiro, personalize o `AGENT.md` substituindo o template genérico por descrição real do seu projeto, sua stack, e suas restrições não-negociáveis específicas. Segundo, crie sua primeira feature em `manifest/features/F-0001-<slug>.md` para a próxima capacidade que você vai construir, mesmo que seja simples. Terceiro, registre seu primeiro ADR em `decisions/0001-<slug>.md` para a primeira decisão arquitetural não-trivial que você fizer; o ADR fundacional sobre adotar a própria metodologia é uma escolha natural.

A partir daí, o uso é orgânico. Cada sessão começa com `memory-bootstrap`, cada commit relevante termina com `memory-debrief`, decisões importantes viram ADRs, e capacidades viram features. A metodologia desaparece no fundo, e o que sobressai é a sensação de que o agente realmente conhece o projeto.
