---
name: memory-deploy
description: Use quando o usuário pede para instalar a metodologia em um projeto (frases como "instale a metodologia", "configure o agent-memory", "rode o setup", "este projeto não tem AGENT.md", "ajude a adotar esta estrutura"), ou quando há merges pendentes de um deploy anterior (frase "resolva os merges pendentes do deploy", presença de arquivo .agent-memory-deploy/merge-queue). Conduz instalação adaptativa: detecta greenfield versus legacy, executa `agent-memory deploy`, mescla arquivos pré-existentes com templates novos preservando customizações, e personaliza ou conduz gênese retroativa conforme o caso.
---

# Memory deploy

Esta skill é o ponto de entrada único para instalar a metodologia em qualquer projeto, e também processa merges pendentes deixados pelo `agent-memory deploy` quando arquivos da metodologia já existiam. Ela conduz o processo completo: deploy mecânico via CLI, merge inteligente quando necessário, e personalização ou gênese retroativa conforme o estado real do projeto.

## Quando usar

A skill aplica-se em três situações distintas. A primeira é quando o usuário pede para instalar a metodologia pela primeira vez, com frases como "instale a metodologia neste projeto", "configure o agent-memory aqui", "rode o setup". A segunda é quando o usuário pede para adotar a metodologia em um projeto legado, com frases como "este projeto não tem AGENT.md" ou "preciso popular o Manifest a partir do código existente". A terceira é quando há merges pendentes de um deploy anterior, sinalizados pela presença do arquivo `.agent-memory-deploy/merge-queue` ou por frases como "resolva os merges pendentes do deploy".

A skill não se aplica quando os artefatos da metodologia já estão totalmente populados e personalizados. Nesse caso use `memory-bootstrap` para retomar trabalho. Também não se aplica quando o usuário quer apenas rodar o deploy mecânico em CI ou automação; nesse caso, `agent-memory deploy <projeto> --no-merge` deve ser invocado diretamente sem mediação de skill.

## Procedimento

A skill executa quatro etapas sequenciais. As duas primeiras são sempre executadas (detecção de estado e deploy mecânico). A terceira ramifica entre merge ou não conforme há fila pendente. A quarta personaliza ou conduz gênese conforme o estado do projeto.

### Etapa 1: detectar o estado do projeto

Examine o projeto para classificá-lo. Os sinais que distinguem greenfield de legacy são objetivos e podem ser checados rapidamente.

Considere o projeto greenfield quando o repositório tem poucos commits (menos de cinco, ou apenas commit inicial), há pouco ou nenhum código (apenas README e arquivos de configuração), e não há entrypoints públicos identificáveis (rotas HTTP, comandos CLI, módulos exportados).

Considere o projeto legacy quando há histórico Git substancial (dez ou mais commits), código de produção em pastas como `src/`, `app/`, `lib/`, stack identificável via arquivos de manifesto, e ausência de `AGENT.md` ou apenas template não-personalizado.

Casos de borda incluem projetos com algum código mas em desenvolvimento ativo recente, que devem ser tratados como legacy se há entrypoints públicos identificáveis. Repositório completamente vazio é greenfield sem ressalvas. Quando ambíguo, pergunte ao usuário em vez de assumir.

Apresente sua classificação e peça confirmação antes de prosseguir. Algo como: "Este parece ser um projeto legado, com 47 commits e código em `src/api/`. Vou conduzir gênese retroativa em quatro fases. Confirma?"

Caso especial: se você foi invocada apenas para resolver merges pendentes (existe `.agent-memory-deploy/merge-queue` mas não é uma instalação nova), pule diretamente para a Etapa 3. A detecção de estado e o deploy já foram feitos antes.

### Etapa 2: executar o deploy mecânico

Em ambos os cenários (greenfield e legacy), rode `agent-memory deploy <projeto>` para estabelecer a estrutura física, onde `<projeto>` é o caminho absoluto da raiz do projeto consumidor. O comando copia templates `AGENT.md` e `CLAUDE.md` para a raiz se ainda não existem ou registra-os como pendentes de merge se existem, copia `STATE.md` se ainda não existe, copia as skills para `skills/`, cria as pastas `manifest/features/` e `decisions/proposals/`, e instala o pre-commit hook se for repositório Git.

Não use `--force` aqui. O `--force` sobrescreve sem mesclagem e perde customizações pré-existentes. Use o comportamento padrão e processe os merges pendentes na próxima etapa.

Se o deploy reportar erros (não confundir com merges pendentes, que não são erros), pare e investigue antes de continuar. Geralmente são problemas de permissão ou Python ausente.

### Etapa 3: processar merges pendentes (se houver)

Após o deploy, verifique se o arquivo `.agent-memory-deploy/merge-queue` existe. Se sim, há arquivos pré-existentes que precisam ser mesclados com os templates novos antes que a personalização da Etapa 4 possa prosseguir.

Para cada arquivo em `.agent-memory-deploy/merge-queue`, leia tanto a versão atual no project root quanto a versão nova em `.agent-memory-deploy/pending/<arquivo>.new`. Aplique a estratégia de merge específica do arquivo descrita abaixo e apresente o resultado para revisão humana antes de gravar.

#### `AGENT.md`: separação entre seções de metodologia e seções de projeto

O `AGENT.md` mistura dois tipos de conteúdo, e o merge trata cada um de forma diferente.

**Seções de metodologia** são idênticas em qualquer projeto e descrevem como a metodologia funciona. Elas devem ser sincronizadas com a versão mais recente do template a cada deploy, porque o template carrega correções e atualizações da própria doutrina:

- O parágrafo introdutório (todo o conteúdo entre `# Constituição do projeto` e o primeiro `##`).
- `## Skills disponíveis`.
- `## Como retomar trabalho`.

**Seções de projeto** são específicas e devem ser preservadas inalteradas a partir do existente. O template não traz placeholders para elas — elas são escritas pela Etapa 4. Quando a Etapa 3 encontra seções já preenchidas, são preservadas como estão:

- `## Identidade`.
- `## Restrições não-negociáveis`.
- `## Convenções de código`.
- Qualquer outra seção `##` que o usuário tenha adicionado e que não esteja na lista de metodologia (preservada intacta — o usuário deve ter tido razão para criá-la).

**Algoritmo do merge**:

1. Faça parse do `AGENT.md` existente em frontmatter + corpo. Quebre o corpo em seções pelos headings `##`. Trate o conteúdo entre `# Constituição do projeto` e o primeiro `##` como uma seção especial chamada "intro".
2. Faça parse do `.new` da mesma forma.
3. **Frontmatter**: união conservadora. Campos só no atual ficam intactos. Campos só no novo são adicionados. Quando há conflito (mesmo campo com valores diferentes), o valor atual prevalece, mas registre o conflito em comentário inline `# template novo sugere: <valor>` para revisão humana. Listas de `constraints` são mescladas pelo `id`: IDs presentes só em um lado são unidos; em colisão de ID, o atual prevalece.
4. **Corpo**: monte na seguinte ordem fixa:
   1. `# Constituição do projeto` + intro do `.new` (sempre da metodologia).
   2. Seções de projeto do existente, na ordem em que apareciam no original.
   3. `## Skills disponíveis` do `.new`.
   4. `## Como retomar trabalho` do `.new`.
5. Se o existente não tinha alguma das seções de projeto esperadas (`## Identidade`, `## Restrições não-negociáveis`, `## Convenções de código`), o resultado do merge fica sem ela. Registre quais estão faltando — a Etapa 4 vai inserir.

Este algoritmo garante três propriedades. Atualizações de metodologia (novas skills documentadas no template, mudanças no fluxo de retomada) chegam a todos os projetos sem intervenção manual. O conteúdo específico do projeto nunca é tocado — não há heurística de comparação por heading, então não há risco de duplicação por concatenação. Seções `##` extras criadas pelo usuário sobrevivem ao merge.

Aviso ao usuário antes de gravar: se ele customizou o conteúdo das seções de metodologia (adicionou notas em `## Skills disponíveis` ou `## Como retomar trabalho`), essas customizações serão perdidas. Sugira mover notas locais para uma seção própria (ex: `## Notas locais sobre skills`) antes de aprovar o merge.

#### `CLAUDE.md`: preservar customizações específicas do Claude Code

Se o template novo é apenas o redirect `@AGENT.md` mas o existente tem conteúdo customizado adicional (instruções específicas para o Claude Code que não fazem sentido em outras ferramentas), preserve o conteúdo customizado e garanta que `@AGENT.md` esteja presente no início. Esta é a única forma do `CLAUDE.md` acumular conteúdo legítimo: instruções que fazem sentido apenas para o Claude Code.

#### Finalização

Apresente cada arquivo mesclado para revisão humana antes de gravar. Mostre as diferenças principais entre o atual e o resultado proposto: o que foi sincronizado da metodologia, o que foi preservado do projeto, o que tem conflito de frontmatter registrado em comentário, e quais seções de projeto ficaram faltando (a Etapa 4 cuida). Quando o usuário aprovar, escreva o resultado no project root e remova os artefatos temporários: o arquivo correspondente em `.agent-memory-deploy/pending/` e a entrada no `.agent-memory-deploy/merge-queue`. Quando todos os arquivos da fila forem processados, remova o diretório `.agent-memory-deploy/` por completo (é gitignored, mas a remoção sinaliza que o handoff foi resolvido).

Após processar todos os merges, rode `agent-memory audit` para validar a estrutura mesclada e gerar os índices.

### Etapa 4a: greenfield — personalização interativa

Esta etapa só executa em projetos greenfield onde os arquivos foram criados do zero (não houve merge). Conduza personalização em diálogo curto com o usuário. Faça perguntas específicas e use as respostas para reescrever o `AGENT.md` antes do primeiro commit.

O template recém-instalado tem apenas mecânica da metodologia (intro, `## Skills disponíveis`, `## Como retomar trabalho`) e um comentário HTML marcando o ponto de inserção das seções de projeto. Sua tarefa é remover esse comentário e inserir três seções entre o intro e `## Skills disponíveis`: `## Identidade`, `## Restrições não-negociáveis`, `## Convenções de código` (esta última pode ser omitida se não há padrões não-óbvios). Mantenha essa ordem.

A primeira pergunta cobre identidade, com algo como "Em uma frase, o que este projeto faz e quem usa?" Use a resposta para escrever a seção `## Identidade`. A segunda pergunta cobre stack: liste o que você detectou em arquivos de configuração e peça confirmação ou correção, atualizando o frontmatter do `AGENT.md` (campo `stack`). A terceira pergunta cobre restrições não-negociáveis, perguntando algo como "Quais são as restrições hard que não podem ser violadas? Por exemplo, ausência de PII em logs, validação obrigatória de schema, requisitos de auditoria." Use as respostas para popular `constraints` no frontmatter e escrever a seção `## Restrições não-negociáveis` espelhando a lista (uma frase por restrição, mencionando o `id`). A quarta pergunta cobre foco inicial, perguntando "Qual é a primeira coisa que você vai construir neste projeto?" Use a resposta para popular `Next` no `STATE.md`.

Ao final, escreva os arquivos personalizados, rode `agent-memory audit` para confirmar que tudo passa, e proponha o commit inicial com mensagem clara como "adopt agent memory methodology".

### Etapa 4b: legacy — gênese retroativa em quatro fases

Esta etapa executa em projetos legacy. Quando houve merge na Etapa 3, parta do `AGENT.md` mesclado em vez de propor um novo do zero — o usuário pode já ter algumas seções de projeto registradas, e a gênese retroativa preenche apenas o que falta.

Fase 1, AGENT.md a partir do código: examine os arquivos de configuração principais — manifestos de dependência, configs de linters e formatadores, CI configs, e READMEs existentes. A partir dessa investigação, prepare três artefatos:

- **Frontmatter**: `stack` (linguagem, arquitetura, banco principal) detectada e `constraints` inferidas dos linters e configs (com `severity: soft` por padrão até o usuário confirmar como hard).
- **Seção `## Identidade`**: 1-2 frases resumindo o que o projeto faz e quem usa, baseado no README e nos entrypoints públicos.
- **Seção `## Restrições não-negociáveis`**: lista narrativa espelhando os `constraints` do frontmatter, com uma frase por restrição mencionando o `id`.
- **Seção `## Convenções de código`** (opcional): apenas se você identificou padrões não-óbvios no código que um agente provavelmente não inferiria. Ausência é aceitável.

Insira as seções no `AGENT.md` entre o parágrafo introdutório e `## Skills disponíveis`, na ordem: Identidade, Restrições, Convenções. Se a Etapa 3 já gravou alguma dessas seções a partir do existente, preserve o que já está lá e preencha apenas as que faltam. Apresente o draft completo para revisão antes de gravar.

Fase 2, ADRs candidatos a partir do git log: rode `agent-memory migrate` para detectar candidatos automáticos. Para cada candidato, examine o commit completo via `git show <sha>` e os arquivos tocados. Avalie se a mudança realmente representa decisão arquitetural ou apenas correção de bug ou refactor mecânico. Para os candidatos que sobrevivem ao filtro, redija um ADR no formato padrão com as quatro seções (Contexto, Decisão, Consequências, Alternativas rejeitadas), usando a data do commit original como `date` e marcando `status: accepted` porque a decisão já está em produção.

Apresente cada ADR proposto individualmente para revisão humana. Não gere uma fila sem aprovação intermediária — o cansaço do revisor é o inimigo. Ao aprovar, escreva diretamente em `decisions/NNNN-slug.md` (não em `proposals/`, porque são reconstruções de decisões já tomadas, não propostas novas).

Fase 3, Manifest a partir dos entrypoints públicos: identifique os entrypoints examinando padrões comuns como routers, handlers e controllers para APIs HTTP, comandos top-level e subcomandos para CLIs, exports principais para bibliotecas, casos de uso ou comandos top-level para serviços. Para cada entrypoint, proponha uma feature com ID monotônico, `status: shipped`, `user_value` baseado no que faz para o usuário (não na implementação técnica), `contracts` apontando para arquivos reais, e `acceptance` em notação EARS inferida do comportamento observável via docstrings, testes existentes ou inferência cuidadosa do código.

Não inclua `metrics` na gênese inicial — métricas só aparecem quando há medições reais. Apresente as features em lotes pequenos (cinco por vez no máximo). Lotes grandes desencorajam revisão crítica.

Fase 4, STATE.md inicial e auditoria: reescreva `STATE.md` com `Current` registrando algo como "Memória inicial estabelecida. Última feature mapeada: F-NNNN." Em `Next`, registre a próxima ação que o usuário tem em mente — pergunte explicitamente, não invente. Em `Recent`, adicione uma linha sobre a gênese com timestamp atual. Deixe `active_features` vazio ou apenas com features em foco no momento. Rode `agent-memory audit` para validar a estrutura completa e sugira o commit inicial.

## Princípios fundamentais

Os princípios abaixo se aplicam a toda a skill, mas são especialmente críticos no fluxo legacy e na fase de merge, onde o risco de erro é maior.

Cristalização silenciosa é o pior erro possível. Em projetos legacy ou em merges, gerar ou sobrescrever conteúdo sem revisão humana cristaliza interpretações erradas como decisões oficiais. Sempre apresente para aprovação antes de gravar em qualquer artefato. Nenhuma economia de tempo justifica esse risco.

Lote pequeno, revisão crítica. Lotes grandes saturam a atenção do revisor e produzem aprovação por cansaço, que é tão ruim quanto cristalização silenciosa. Limite a cinco itens por rodada de aprovação.

Quando em dúvida, não escreva. Em merges, isso significa preservar o conteúdo existente em vez de modificá-lo. Em gênese, significa deixar uma feature ou ADR fora da gênese inicial em vez de escrevê-la imprecisa.

Conteúdo do usuário é sagrado. Em qualquer fase de merge, o conteúdo pré-existente do usuário tem prioridade sobre o template novo. O template fornece estrutura; o usuário fornece substância. Quando há conflito, o usuário ganha por padrão, com o template registrado em comentário para revisão.

## O que evitar

Não rode `agent-memory deploy --force` automaticamente. O `--force` é uma escolha consciente do operador para sobrescrever sem merge, e a skill deve respeitar essa escolha apenas quando o usuário pede explicitamente.

Não tente cobrir cem por cento das decisões históricas ou dos entrypoints na primeira gênese. Capture o que é claro e importante; o resto entra incrementalmente conforme o trabalho normal toca essas áreas. Cobertura parcial honesta é melhor que cobertura total inventada.

Não invente `metrics` ou medições estimadas. Se não há valor real medido, omita o campo. Métricas inventadas comprometem a credibilidade do Manifest todo.

Não inclua features para detalhes de implementação puramente internos. A unidade do Manifest é capacidade nomeável com `user_value` em uma frase.

Não confunda os dois fluxos de criação de ADR. Na gênese retroativa, ADRs vão diretamente para `decisions/` porque são reconstruções históricas. Em uso normal (skill `memory-debrief`), ADRs novos vão para `decisions/proposals/` primeiro.

Não esqueça de limpar os artefatos temporários após o merge. Os arquivos `.agent-memory-deploy/merge-queue` e `.agent-memory-deploy/pending/` existem apenas para coordenar o handoff entre o script e a skill. Após processar todos os merges, eles devem ser removidos.
