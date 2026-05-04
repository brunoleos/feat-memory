---
id: ADR-0019
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0015]
related: [ADR-0018, ADR-0001]
tags: [state, checkpoint, schema, migration]
---

# ADR-0019 · Formato canônico do checkpoint e migração de consumidores existentes

## Contexto

ADR-0018 estabeleceu o modelo append-only com `STATE.md` como view. Esta decisão preenche os detalhes mecânicos: como cada checkpoint é nomeado, qual o schema do frontmatter, qual o algoritmo de migração para consumidores que já têm `STATE.md` populado. Sem isso, ADR-0018 fica abstrato e a implementação fica ad-hoc.

Decisões em jogo: (a) convenção de nome do arquivo, (b) campos obrigatórios e opcionais do frontmatter, (c) o que fazer com o `STATE.md` legado de quem está fazendo upgrade.

## Decisão

### Nome do arquivo

`.agent-memory/checkpoints/YYYY-MM-DD-HHMMSS.md`. Timestamp UTC, formato fixo, ordenação lexicográfica = ordenação temporal (propriedade que justifica o formato escolhido — fica trivial pegar "o mais recente" via `sorted(glob)[-1]`).

Em casos de colisão (dois checkpoints no mesmo segundo, raríssimo), sufixa com `-N` incremental — `2026-05-04-153042-1.md`. Sem isso, sobrescrita silenciosa: a propriedade de imutabilidade quebra. O resolvedor de colisão é o próprio comando `agent-memory checkpoint`, transparente para o chamador.

### Schema do frontmatter

```yaml
---
schema_version: 1
ts: 2026-05-04T15:30:42+00:00
author: claude-opus-4.7
active_features: [F-0001, F-0002]
active_decisions: [ADR-0001]
blocked_on: null
current: "implementação de F-0010 em curso, falta wiring no deploy"
next: "ligar deploy_meta no run() e rodar testes"
summary: "F-0010: wiring do deploy_meta..."
---

(corpo livre — notas do agente, links, raciocínio)
```

Campos obrigatórios: `schema_version`, `ts`, `author`, `current`, `next`, `summary`. Campos opcionais com default: `active_features=[]`, `active_decisions=[]`, `blocked_on=null`.

`schema_version` independente do schema do STATE.md (vive em `1` aqui, `2` no STATE.md). Permite evolução isolada.

`current` e `next` são strings de uma frase — são interpoladas direto nas seções `## Current` e `## Next` do STATE.md gerado. `summary` é mais flexível (uma a três frases) e alimenta a tabela `Recent`.

O corpo (markdown após o frontmatter) é livre. Notas, raciocínio, links a recursos externos. A geração de STATE.md ignora o corpo — ele existe para consulta humana e contexto de retomada estendida quando necessário.

### Comando `agent-memory checkpoint`

```
agent-memory checkpoint
    --summary "..."         (obrigatório)
    --current "..."         (default: igual ao summary)
    --next "..."            (default: campo current do checkpoint anterior, ou "TODO")
    --features F-0001,F-0002,...   (opcional; default: do checkpoint anterior)
    --decisions ADR-0001,...       (opcional; default: do checkpoint anterior)
    --blocked-on "..."             (opcional; default: do checkpoint anterior)
    --author NAME                  (opcional; default: detectado do contexto)
```

Anexa novo checkpoint, depois invoca o renderer de STATE.md. Idempotência: dois checkpoints com mesmo conteúdo gravados em sequência geram dois arquivos diferentes (timestamps diferentes); o segundo simplesmente reflete o estado vigente, sem tratamento especial — se o ritual debriefou duas vezes, é honesto registrar isso.

### Comando `agent-memory state-rebuild`

Re-renderiza `STATE.md` a partir dos checkpoints existentes, sem criar novo. Recovery após edição manual indevida do STATE.md (que não faz mais parte do fluxo, mas é o caminho de "concertar" se alguém errou).

### Migração de consumidores existentes

Novo modo `agent-memory migrate --to=checkpoints`:

1. Detecta se `.agent-memory/checkpoints/` já existe e tem arquivos. Se sim, idempotente — emite mensagem e sai.
2. Lê o `STATE.md` atual. Extrai `updated_at` (vira `ts`), `updated_by` (vira `author`), `active_features`, `active_decisions`, `blocked_on`.
3. Extrai a primeira linha não-vazia da seção `## Current` (vira `current` do checkpoint).
4. Extrai a primeira linha não-vazia da seção `## Next` (vira `next` do checkpoint).
5. Concatena `Current` + `Next` num parágrafo curto que vira `summary`.
6. O corpo do STATE original (a tabela `Recent` em particular) é preservado como corpo do checkpoint inicial — preserva história sem ter que fabricar checkpoints retroativos para cada linha.
7. Após gravar o checkpoint inicial, invoca o renderer de STATE.md.

Observação: a tabela `Recent` legada agora vive como markdown no corpo do primeiro checkpoint (informação histórica preservada para consulta), e o renderer começa um `Recent` novo a partir do segundo checkpoint em diante.

`migrate --to=checkpoints` é não-destrutivo: nunca apaga o `STATE.md` original (só o regenera com mesmo conteúdo, agora derivado do checkpoint).

## Consequências

**Positivas**:

- Convenção de nome ordenável lex evita necessidade de parser de timestamps no caminho crítico de "qual é o mais recente". `sorted(checkpoints/*.md)[-1]` é canônico.
- Schema versionado (`schema_version: 1`) permite mudança futura sem quebrar leitores antigos.
- Migração explícita via `migrate --to=checkpoints` (vs migração automática no primeiro debrief) dá controle ao mantenedor — ele decide quando começar a usar o novo modelo. Idempotência cobre re-execução acidental.
- Preservação da tabela `Recent` legada no corpo do primeiro checkpoint mantém história sem fabricar dados (não há como reconstruir checkpoints retroativos com fidelidade — preservar como prosa é honesto).
- Distinção clara entre `current` (frase única) e `summary` (parágrafo) dá ao agente liberdade de granularidade. STATE.md fica conciso (`Current` é curto), enquanto `Recent` ganha profundidade.

**Negativas**:

- Resolução de colisão por sufixo `-N` é uma micro-feature pra um caso raríssimo. Aceito por imperativo de imutabilidade — a alternativa (sobrescrever) seria silenciosa e catastrófica.
- Schema com 6 campos obrigatórios é mais barreira do que `STATE.md` plano. Mitigado pela skill `memory-debrief` que monta a invocação completa do `checkpoint` sem o usuário ter que lembrar dos flags.
- O corpo do checkpoint inicial (preservando `Recent` legado) é heterogêneo — checkpoints subsequentes terão corpos curtos ou vazios. Esperado e aceito.

## Alternativas rejeitadas

**Nome do arquivo só com timestamp Unix epoch (`1714838442.md`)**. Ordenação numérica = ordenação temporal, mais compacto. Rejeitada porque humanos lendo `ls` ganham nada com isso e perdem legibilidade. ISO 8601 é universalmente legível.

**Arquivos `.json` em vez de markdown**. Schema mais explícito, parsers nativos. Rejeitada porque o corpo livre em prosa é um valor central — JSON forçaria string única ou perderia a flexibilidade. Markdown com frontmatter é o mesmo padrão de features e ADRs do projeto, coerência vence.

**Migração automática no primeiro `agent-memory checkpoint` se `checkpoints/` está vazio**. Conveniente, mas surpresa. O mantenedor pode estar testando, e migrar STATE.md sem aviso é invasivo. Comando explícito é mais previsível. Rejeitada por princípio do menor surpresa.

**Migração apaga STATE.md e força regeneração subsequente**. Mais limpo conceitualmente. Rejeitada porque criaria diff Git desnecessário (apaga + recria) e abre janela de erro se a regeneração falhar. Não-destrutivo é mais seguro.

**Exigir `current`, `next` E `summary` como obrigatórios sem defaults**. Mais estrito. Rejeitada porque a UX da skill ficaria horrível (o agente teria que sempre especificar `next` mesmo quando é continuação trivial). Default "puxar do checkpoint anterior" mantém o esforço marginal de cada novo checkpoint pequeno.
