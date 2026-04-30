---
id: ADR-0011
date: 2026-04-30
status: proposed
supersedes: ADR-0010
superseded_by: null
affects_features: [F-0001, F-0006]
related: [ADR-0010]
tags: [deploy, sentinels, scope, skill]
---

# ADR-0011 · Deploy gerencia metodologia em AGENT.md via bloco com sentinelas markdown

## Contexto

ADR-0010 separou seções de metodologia (sincronizadas a partir do template) de seções de projeto (preservadas a partir do existente) no merge da `AGENT.md`. O algoritmo identificava seções por seus headings (`## Skills disponíveis`, `## Como retomar trabalho`, etc.) e aplicava regras diferentes a cada categoria. Funcionava, mas tinha três problemas práticos.

Primeiro, **a skill ainda autoraba conteúdo de projeto** durante a Etapa 4 (personalização ou gênese retroativa Fase 1) — identidade, restrições, convenções. ADR-0011 (versão anterior, descartada) atacou esse sintoma reduzindo o escopo da Etapa 4 a popular só o frontmatter, mas a skill continuava grudada na noção de "qual seção é minha vs. do usuário".

Segundo, **a separação metodologia/projeto vivia em prosa no `SKILL.md`** como uma lista de headings explicitamente categorizada. Adicionar uma seção de metodologia nova exigiria atualizar o template, o `SKILL.md`, e propagar via re-deploy — três pontos de mudança coordenados, frágeis a divergência.

Terceiro, **o merge ainda envolvia handoff intermediário** via `.agent-memory-deploy/merge-queue` e `pending/AGENT.md.new`. O `agent-memory deploy` empilhava o template novo, e a skill `memory-deploy` Etapa 3 fazia o merge. Mecânica em duas etapas que precisava de coerência entre CLI e agente para chegar ao estado final.

A reflexão sobre essas três frições — autoria de conteúdo, taxonomia em prosa, handoff intermediário — apontou para uma simplificação radical: **o deploy não precisa entender semântica de seções**. Se a metodologia inteira viver dentro de um bloco delimitado por sentinelas, o deploy só precisa fazer find-and-replace do bloco; tudo que está fora é do usuário, sem qualquer categorização. É o mesmo padrão que `.gitattributes` e `.gitignore` já usam neste mesmo projeto.

## Decisão

A `AGENT.md` carrega um bloco delimitado por sentinelas markdown (HTML comments):

```markdown
<!-- >>> agent-memory >>> -->
## agent-memory

[intro com referências a STATE.md, manifest/, decisions/]

### Skills disponíveis

[descrição das três skills]

### Como retomar trabalho

[fluxo de retomada]
<!-- <<< agent-memory <<< -->
```

O `agent-memory deploy` (F-0001) gerencia esse bloco mecanicamente:

- `AGENT.md` ausente: escreve o template completo (frontmatter scaffold + heading + bloco com sentinelas).
- `AGENT.md` existe e tem o bloco: substitui o conteúdo entre as sentinelas pelo conteúdo extraído do template novo. Tudo fora das sentinelas é preservado byte-a-byte.
- `AGENT.md` existe sem o bloco: anexa o bloco ao final.

A função `_replace_sentinel_block` (já existente no `deploy.py` para `.gitattributes`/`.gitignore`) é parameterizada para aceitar pares de sentinelas customizados; a mesma máquina serve para markdown e shell.

A skill `memory-deploy` (F-0006) perde duas das suas etapas anteriores. Etapa 3 (merge) some inteira — o deploy resolve o bloco sozinho, sem handoff intermediário. Etapa 4 (personalização/gênese de seções de AGENT.md) também some — o deploy só toca o bloco, e identidade/restrições/convenções são autoria do mantenedor humano fora do bloco. A skill fica com três etapas: detectar greenfield/legacy, executar `agent-memory deploy`, e (em projetos legacy) gênese retroativa de ADRs em `decisions/` e features em `manifest/`. O frontmatter da `AGENT.md` deixa de ser populado pela skill — o template fornece scaffold com defaults exemplares, e o usuário edita.

O mecanismo de merge-queue (`.agent-memory-deploy/merge-queue` e `pending/`) é eliminado. O diretório legado é removido na primeira execução pós-upgrade para evitar acúmulo.

ADR-0010 fica `superseded_by: ADR-0011`. O algoritmo de comparação por heading proposto lá nunca foi exercitado em produção (foi imediatamente substituído por esta abordagem), então não há débito de migração — só obsolescência conceitual.

## Consequências

**Positivas**:

- O deploy não tem mais opinião sobre conteúdo de projeto. Ele administra um bloco e ponto. Toda a complexidade de "qual seção é minha" desaparece.
- Adoção mais rápida em greenfield: zero perguntas. `agent-memory deploy <projeto>` instala a estrutura, e o mantenedor edita o que quiser quando quiser.
- Re-deploys são genuinamente idempotentes e não-destrutivos: rodar `agent-memory deploy` num projeto pós-upgrade só refresca o bloco. Atualizações da metodologia (skills novas documentadas, mudanças no fluxo de retomada) propagam automaticamente.
- Menos superfície na skill `memory-deploy`. SKILL.md encolhe; menos coisa para o agente entender; menos pontos de divergência entre o que a skill diz e o que o `deploy.py` faz.
- O mantenedor humano tem liberdade total fora do bloco: pode ter `AGENT.md` minimalista (só frontmatter + bloco), pode escrever várias seções específicas, pode mover o bloco para o início ou fim do arquivo — nada disso afeta o deploy.
- Defesa em profundidade contra menções literais às sentinelas no conteúdo: `_replace_sentinel_block` e `_extract_methodology_block` usam `partition` para a abertura e `rpartition` para o fechamento, casando com a primeira ocorrência da abertura e a última do fechamento. Isso evita corrupção quando o conteúdo do bloco menciona as strings das sentinelas (caso encontrado e corrigido durante a implementação desta decisão).

**Negativas**:

- Se o usuário menciona literalmente a string `<!-- >>> agent-memory >>> -->` no conteúdo (fora do bloco), pode confundir o deploy. Mitigado pela escolha de strings improváveis e pelo `partition`/`rpartition` que toleram menções dentro do conteúdo do bloco. Caso de borda muito raro na prática.
- A skill perde o caminho de "interrogar o usuário sobre identidade durante a adoção". Ganhamos em previsibilidade e respeito à autoria humana, mas alguns mantenedores podem preferir o fluxo conversacional. Mitigação: o usuário pode sempre pedir ajuda em qualquer turno fora da skill ("escreva uma seção de identidade pra mim baseada no README"), invocando o agente fora do escopo de adoção.
- Backward compatibility: projetos que adotaram via versões anteriores (v0.3.x ou anteriores) têm `AGENT.md` sem sentinelas. No próximo `agent-memory deploy` pós-upgrade, o bloco é anexado ao fim do arquivo, e o conteúdo de metodologia que estava em seções H2 separadas (Skills disponíveis, Como retomar trabalho) fica duplicado. O mantenedor remove as seções antigas manualmente. Aceito como custo único de migração.
- ADRs anteriores (0010, 0011 versão antiga) ficam como histórico conceitual sem produção real. Isto é o que `superseded` é para: registrar que uma direção foi explorada e abandonada antes de gerar dependências.

## Alternativas rejeitadas

**Manter a separação metodologia/projeto baseada em headings** (status quo de ADR-0010). Funciona mas mantém a skill com opinião sobre conteúdo de projeto e mantém o handoff via merge-queue. A simplificação do bloco com sentinelas remove ambos os problemas com menos código. Rejeitada por dívida arquitetural sem justificativa.

**Mover toda a metodologia para um arquivo separado importado por `@`** (ex: `@AGENT_METHODOLOGY.md`). Tornaria o deploy ainda mais simples (sobrescrever um arquivo só), mas viola a convenção de que `AGENT.md` é o único arquivo carregado automaticamente por ferramentas multi-agente. Sentinelas dentro de `AGENT.md` mantêm a convenção e atingem o mesmo objetivo. Rejeitada por custo arquitetural.

**Não refrescar o bloco em re-deploys** ("instala uma vez, usuário cuida dali em diante"). Considerada e descartada na conversa: rompe o mecanismo de propagação automática de atualizações da metodologia, que é parte do valor da tool ser editable install/pipx. Rejeitada por jogar fora valor.

**Achar o bloco por heading** (`## agent-memory`) em vez de sentinelas. Funciona se o heading for estável, mas o usuário pode renomear (válido — é arquivo dele). Sentinelas são strings improváveis que documentam claramente o contrato. Tradeoff explícito: duas linhas de comentário HTML invisíveis na renderização vs. fragilidade. Sentinelas vencem. Rejeitada.

**Gerar drafts com placeholder e deixar o usuário editar** (proposta original, antes desta sessão). Reabriria o problema que ADR-0010 atacou: distinção entre placeholder e conteúdo é frágil. Esta abordagem (sentinelas) é estritamente mais simples. Rejeitada por reintroduzir bug.
