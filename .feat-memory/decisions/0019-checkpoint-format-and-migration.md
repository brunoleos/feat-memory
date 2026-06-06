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

# ADR-0019 · Formato canônico do checkpoint e migração

## Contexto

ADR-0018 fixou o modelo append-only. Esta decisão preenche os detalhes mecânicos: nome do arquivo, schema do frontmatter, e algoritmo de migração para consumidores com `STATE.md` populado.

## Decisão

**Nome:** `.feat-memory/checkpoints/YYYY-MM-DD-HHMMSS.md` (UTC, formato fixo, ordenação lex = ordenação temporal — `sorted(glob)[-1]` pega o mais recente). Colisão: sufixo `-N` incremental, resolvido pelo próprio comando.

**Schema do frontmatter** (`schema_version: 1`, independente do STATE.md):

- Obrigatórios: `schema_version`, `ts`, `author`, `current`, `next`, `summary`.
- Opcionais com default: `active_features=[]`, `active_decisions=[]`, `blocked_on=null`.
- `current`/`next` são frases únicas (alimentam seções do STATE.md). `summary` 1-3 frases (alimenta `Recent`). Corpo livre — notas, raciocínio, links; ignorado pelo gerador de STATE.md.

**Comando:** `feat-memory checkpoint --summary "..." [--current ...] [--next ...] [--features ...] [--decisions ...] [--blocked-on ...] [--author ...]`. Flags omitidas herdam do checkpoint anterior (continuidade trivial); sem anterior, defaults sensatos (`current=summary`, `next="TODO"`).

**`feat-memory state-rebuild`:** regenera STATE.md a partir dos checkpoints existentes sem criar novo (recovery).

**Migração** (`feat-memory migrate --to=checkpoints`): idempotente; detecta `checkpoints/` populado e sai. Caso contrário lê STATE.md legado, extrai `updated_at`→`ts`, `updated_by`→`author`, `active_*`, `blocked_on`, primeira linha de Current/Next, concatena em `summary`. Preserva body legado (incluindo tabela Recent) no body do primeiro checkpoint. Não-destrutivo — nunca apaga STATE.md (regenera com conteúdo equivalente derivado do checkpoint).

## Alternativas rejeitadas

- **Timestamp Unix epoch (`1714838442.md`)**: humanos lendo `ls` perdem legibilidade; ISO 8601 é universalmente legível.
- **JSON em vez de markdown**: forçaria corpo livre como string ou perderia flexibilidade; markdown com frontmatter é o padrão do projeto.
- **Migração automática no primeiro `checkpoint`**: invasivo; mantenedor pode estar testando.
- **Migração apaga STATE.md e força regeneração**: diff Git desnecessário + janela de erro; não-destrutivo é mais seguro.
- **`current`+`next`+`summary` todos obrigatórios sem defaults**: UX horrível; default "puxar do anterior" mantém esforço marginal pequeno.
