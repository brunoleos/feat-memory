---
name: memory-deploy
description: Use quando o usuário pede para instalar a metodologia em um projeto (frases como "instale a metodologia", "configure o agent-memory", "rode o setup", "este projeto não tem AGENT.md", "ajude a adotar esta estrutura"). Conduz a adoção: detecta greenfield versus legacy, executa `agent-memory deploy` (que cuida sozinho do bloco com sentinelas no AGENT.md), e em projetos legacy faz gênese retroativa de ADRs e Manifest a partir do git log e dos entrypoints públicos. Não escreve em AGENT.md fora do bloco delimitado pelas sentinelas.
---

# Memory deploy

Esta skill é o ponto de entrada único para instalar a metodologia em qualquer projeto. Conduz três etapas: detecção do estado do projeto, deploy mecânico via CLI, e (apenas em projetos legacy) gênese retroativa de ADRs e do Manifest.

A skill **não escreve no corpo da `AGENT.md`** fora do bloco delimitado pelas sentinelas markdown. O bloco em si é gerenciado pelo `agent-memory deploy` (refrescado a cada execução). Identidade, restrições não-negociáveis, convenções de código e qualquer outra seção específica do projeto são autoria do mantenedor humano, registradas em sessão posterior se ele decidir que vale.

## Quando usar

A skill aplica-se em duas situações. A primeira é quando o usuário pede para instalar a metodologia pela primeira vez, com frases como "instale a metodologia neste projeto", "configure o agent-memory aqui", "rode o setup". A segunda é quando o usuário pede para adotar a metodologia em um projeto legado, com frases como "este projeto não tem AGENT.md" ou "preciso popular o Manifest a partir do código existente".

A skill não se aplica quando os artefatos da metodologia já estão totalmente populados. Nesse caso use `memory-bootstrap` para retomar trabalho. Também não se aplica quando o usuário quer apenas rodar o deploy mecânico em CI ou automação; nesse caso, `agent-memory deploy <projeto> --no-merge` deve ser invocado diretamente sem mediação de skill.

## Procedimento

A skill executa três etapas sequenciais. As duas primeiras são sempre executadas. A terceira só roda em projetos legacy.

### Etapa 1: detectar o estado do projeto

Examine o projeto para classificá-lo. Os sinais que distinguem greenfield de legacy são objetivos e podem ser checados rapidamente.

Considere o projeto greenfield quando o repositório tem poucos commits (menos de cinco, ou apenas commit inicial), há pouco ou nenhum código (apenas README e arquivos de configuração), e não há entrypoints públicos identificáveis (rotas HTTP, comandos CLI, módulos exportados).

Considere o projeto legacy quando há histórico Git substancial (dez ou mais commits), código de produção em pastas como `src/`, `app/`, `lib/`, stack identificável via arquivos de manifesto, e ausência de `AGENT.md` ou apenas template não-personalizado.

Casos de borda incluem projetos com algum código mas em desenvolvimento ativo recente, que devem ser tratados como legacy se há entrypoints públicos identificáveis. Repositório completamente vazio é greenfield sem ressalvas. Quando ambíguo, pergunte ao usuário em vez de assumir.

Apresente sua classificação e peça confirmação antes de prosseguir. Algo como: "Este parece ser um projeto legado, com 47 commits e código em `src/api/`. Vou rodar o deploy e depois fazer gênese retroativa de ADRs e Manifest. Confirma?"

### Etapa 2: executar o deploy mecânico

Em ambos os cenários (greenfield e legacy), rode `agent-memory deploy <projeto>` para estabelecer a estrutura física, onde `<projeto>` é o caminho absoluto da raiz do projeto consumidor. O comando:

- Cria `AGENT.md` com frontmatter scaffold + bloco com sentinelas, ou — se já existe — anexa o bloco preservando todo o resto do conteúdo do usuário. Em re-deploys, o bloco é refrescado de forma idempotente.
- Cria `CLAUDE.md` (redirect mínimo `@AGENT.md`) se ausente; deixa quieto se existe.
- Cria `.agent-memory/STATE.md` se ausente.
- Copia as skills para `skills/` (sempre sobrescritas; conteúdo de metodologia).
- Cria pastas `.agent-memory/manifest/features/` e `.agent-memory/decisions/proposals/`.
- Instala o pre-commit hook se for repositório Git.
- Refresca os blocos de `.gitattributes` e `.gitignore`.

Não use `--force` aqui. O `--force` reescreve `AGENT.md` inteira a partir do template, perdendo conteúdo do usuário fora do bloco. O comportamento padrão (sentinel-block refresh) é o que você quer para adoção.

Se o deploy reportar erros, pare e investigue. Geralmente são problemas de permissão ou Python ausente.

A partir deste ponto a skill não escreve mais em `AGENT.md`. Em greenfield, o trabalho da skill termina aqui — sugira commitar o estado inicial. Em legacy, prossiga para a Etapa 3.

### Etapa 3 (apenas legacy): gênese retroativa de ADRs e Manifest

Esta etapa só executa em projetos legacy. Ela popula `.agent-memory/decisions/` e `.agent-memory/manifest/features/` a partir do que já existe no repositório, mas **não toca em `AGENT.md`**. Identidade, restrições e convenções específicas do projeto continuam sendo responsabilidade do mantenedor humano, em sessão posterior.

#### Fase 3.1: ADRs candidatos a partir do git log

Rode `agent-memory migrate` para detectar candidatos automáticos. Para cada candidato, examine o commit completo via `git show <sha>` e os arquivos tocados. Avalie se a mudança realmente representa decisão arquitetural ou apenas correção de bug ou refactor mecânico. Para os candidatos que sobrevivem ao filtro, redija um ADR no formato padrão com as quatro seções (Contexto, Decisão, Consequências, Alternativas rejeitadas), usando a data do commit original como `date` e marcando `status: accepted` porque a decisão já está em produção.

Apresente cada ADR proposto individualmente para revisão humana. Não gere uma fila sem aprovação intermediária — o cansaço do revisor é o inimigo. Ao aprovar, escreva diretamente em `.agent-memory/decisions/NNNN-slug.md` (não em `proposals/`, porque são reconstruções de decisões já tomadas, não propostas novas).

#### Fase 3.2: Manifest a partir dos entrypoints públicos

Identifique os entrypoints examinando padrões comuns como routers, handlers e controllers para APIs HTTP, comandos top-level e subcomandos para CLIs, exports principais para bibliotecas, casos de uso ou comandos top-level para serviços. Para cada entrypoint, proponha uma feature com ID monotônico, `status: shipped`, `user_value` baseado no que faz para o usuário (não na implementação técnica), `contracts` apontando para arquivos reais, e `acceptance` em notação EARS inferida do comportamento observável via docstrings, testes existentes ou inferência cuidadosa do código.

Não inclua `metrics` na gênese inicial — métricas só aparecem quando há medições reais. Apresente as features em lotes pequenos (cinco por vez no máximo). Lotes grandes desencorajam revisão crítica.

#### Fase 3.3: `.agent-memory/STATE.md` inicial e auditoria

Reescreva `.agent-memory/STATE.md` com `Current` registrando algo como "Memória inicial estabelecida via gênese retroativa. Última feature mapeada: F-NNNN." Em `Next`, escreva uma frase neutra do tipo "Aguardando definição do próximo foco pelo usuário." — não pergunte ao usuário e não invente um foco; ele rescreve quando começar a trabalhar. Em `Recent`, adicione uma linha sobre a gênese com timestamp atual. Deixe `active_features` vazio ou apenas com features em foco no momento.

Rode `agent-memory audit` para validar a estrutura completa e sugira o commit inicial.

## Princípios fundamentais

Cristalização silenciosa é o pior erro possível. Em qualquer fase de gênese (Etapa 3), gerar ADRs ou features sem revisão humana cristaliza interpretações erradas como decisões oficiais. Sempre apresente para aprovação antes de gravar em qualquer artefato. Nenhuma economia de tempo justifica esse risco.

Lote pequeno, revisão crítica. Lotes grandes saturam a atenção do revisor e produzem aprovação por cansaço, que é tão ruim quanto cristalização silenciosa. Limite a cinco itens por rodada de aprovação.

Quando em dúvida, não escreva. Em gênese, isso significa deixar uma feature ou ADR fora da gênese inicial em vez de escrevê-la imprecisa.

A skill nunca escreve no corpo da `AGENT.md` fora do bloco com sentinelas. Mesmo que o usuário peça explicitamente "preencha a identidade" durante a adoção, recuse: identidade do projeto é autoria humana e o usuário pode escrever no próximo turno fora desta skill.

## O que evitar

Não rode `agent-memory deploy --force` automaticamente. O `--force` reescreve `AGENT.md` do template, perdendo conteúdo do usuário fora do bloco com sentinelas. É escolha consciente do operador, e a skill deve respeitar essa escolha apenas quando o usuário pede explicitamente.

Não tente cobrir cem por cento das decisões históricas ou dos entrypoints na primeira gênese. Capture o que é claro e importante; o resto entra incrementalmente conforme o trabalho normal toca essas áreas. Cobertura parcial honesta é melhor que cobertura total inventada.

Não invente `metrics` ou medições estimadas. Se não há valor real medido, omita o campo. Métricas inventadas comprometem a credibilidade do Manifest todo.

Não inclua features para detalhes de implementação puramente internos. A unidade do Manifest é capacidade nomeável com `user_value` em uma frase.

Não confunda os dois fluxos de criação de ADR. Na gênese retroativa, ADRs vão diretamente para `.agent-memory/decisions/` porque são reconstruções históricas. Em uso normal (skill `memory-debrief`), ADRs novos vão para `.agent-memory/decisions/proposals/` primeiro.
