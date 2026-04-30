---
id: ADR-0010
date: 2026-04-30
status: proposed
supersedes: null
superseded_by: null
affects_features: [F-0001, F-0006]
related: []
tags: [deploy, merge, template, skill]
---

# ADR-0010 · Merge de AGENT.md separa seções de metodologia (sincronizadas) de seções de projeto (preservadas)

## Contexto

A skill `memory-deploy` (F-0006) é responsável por mesclar o `AGENT.md` existente do projeto consumidor com o template novo entregue por `agent-memory deploy` (F-0001). A regra original instruía: "seções que existem apenas no template novo são adicionadas ao final, marcadas com comentário".

O usuário observou na prática que, quando o `AGENT.md` existente já tinha conteúdo real em `## Identidade` (preenchido em uma sessão anterior) e o template novo carregava `## Identidade` como placeholder ("Descreva aqui em uma ou duas frases..."), o agente concatenava o template inteiro ao final, produzindo um arquivo com seções duplicadas.

A causa raiz é mais profunda do que um bug de comparação por heading: o template misturava dois tipos de conteúdo com semântica de merge incompatível. Mecânica da metodologia (intro, descrição das três skills, fluxo de retomada) é doutrina que evolui com a tool e deve propagar para todos os projetos via re-deploy. Conteúdo específico do projeto (identidade, restrições, convenções) é o oposto: é escrito uma vez pelo agente durante a personalização e não deve ser tocado depois. Tratar ambos com a mesma regra de merge é o que produz o bug — qualquer heurística baseada em comparação textual de seções vai falhar nas bordas.

## Decisão

Separar as seções do `AGENT.md` em duas categorias com regras de merge distintas, codificadas explicitamente no `SKILL.md`:

**Seções de metodologia** (sempre sincronizadas a partir do template novo):

- O parágrafo introdutório (entre `# Constituição do projeto` e o primeiro `##`).
- `## Skills disponíveis`.
- `## Como retomar trabalho`.

**Seções de projeto** (sempre preservadas a partir do existente):

- `## Identidade`.
- `## Restrições não-negociáveis`.
- `## Convenções de código`.
- Qualquer outra seção `##` adicionada pelo usuário.

O template não carrega mais placeholders para as seções de projeto — apenas um comentário HTML marcando o ponto de inserção. A skill escreve essas seções a partir da investigação durante a Etapa 4 (personalização ou gênese retroativa). O frontmatter mantém a estratégia anterior de união conservadora (existente vence em conflito; constraints mescladas por `id`).

A ordem do resultado é fixa: intro → seções de projeto (na ordem original do existente) → Skills disponíveis → Como retomar trabalho.

## Consequências

**Positivas**:

- O merge é determinístico e auditável. Não há mais comparação por heading nem heurística de "adiciona ao final" — a posição de cada categoria de seção é fixa.
- Atualizações da metodologia (novas skills documentadas, mudanças no fluxo de retomada) propagam para todos os projetos consumidores via re-deploy, sem intervenção humana.
- Conteúdo específico do projeto é sacred — nunca tocado pelo merge.
- Seções `##` extras criadas pelo usuário (ex: notas locais sobre práticas internas) sobrevivem ao merge porque caem na categoria de projeto.
- A coupling entre F-0001 (que entrega o template) e F-0006 (que consome a estrutura do template) fica explícito no Manifest: a estrutura do `data/templates/AGENT.md` é agora um contrato compartilhado.

**Negativas**:

- Customizações dentro das seções de metodologia (ex: usuário acrescenta notas em `## Como retomar trabalho`) são perdidas no merge. Mitigação: a skill avisa o usuário antes de gravar e sugere mover notas locais para uma seção própria (ex: `## Notas locais sobre skills`).
- Fresh deploy produz um `AGENT.md` estruturalmente incompleto (sem seções de projeto) até a Etapa 4 rodar. Mitigação: comentário HTML marcador deixa o gap visível, e a Etapa 4 é parte do mesmo fluxo da skill.
- A lista de quais headings são metodologia vs projeto vive no `SKILL.md` em prosa, não em código. Adicionar uma seção de metodologia nova requer atualizar o template, o `SKILL.md`, e — se a categorização mudar — propagar via re-deploy. O custo é aceitável dado o ganho em previsibilidade.

## Alternativas rejeitadas

**Manter placeholders no template e melhorar a heurística de comparação**. Foi a abordagem original e gerou o bug. Qualquer heurística que dependa de detectar "esta seção é placeholder" versus "esta seção tem conteúdo real" é frágil — formatação ligeiramente diferente do placeholder já quebra a detecção. Rejeitada como falsa economia.

**Mover a mecânica da metodologia para um arquivo separado importado via `@METHODOLOGY_INSTRUCTIONS.md`**. Tornaria o merge trivial (o arquivo separado é sempre sobrescrito pelo deploy), mas quebra a convenção de que `AGENT.md` é um arquivo único e auto-contido — convenção que justifica o nome do projeto e a portabilidade entre ferramentas (Claude Code, Cursor, Aider). Rejeitada por custo arquitetural alto.

**Usar marcadores HTML dentro do próprio template para delimitar regiões sync vs preserve** (ex: `<!-- agent-memory:sync-start -->`...`<!-- agent-memory:sync-end -->`). Funciona, mas polui o artefato com sintaxe interna da tool, e o usuário pode remover marcadores acidentalmente, quebrando o merge. A convenção por heading (codificada no `SKILL.md`) atinge o mesmo objetivo sem invasão. Rejeitada.

**Dropar `## Identidade` do template (proposta inicial do usuário)**. A seção é valiosa: é o primeiro contato que um agente tem com o domínio do projeto, antes mesmo das restrições mecânicas. O problema não era a seção, era o placeholder dentro dela. Mantida a seção, removido apenas o placeholder. Rejeitada por ser correção excessiva para um sintoma do bug, não a causa.
