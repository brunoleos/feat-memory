---
name: memory-debrief
description: Use quando o usuário sinaliza intenção de commitar, fechar sessão, ou pedir atualização da memória do projeto (frases como "vou commitar", "atualize o STATE", "feche a sessão", "debrief", "antes de subir"). Examina o diff, atualiza entradas do Manifest, reescreve STATE.md, e gera proposta de ADR se a sessão produziu decisão arquitetural.
---

# Memory debrief

Quando o usuário sinaliza fim de uma unidade de trabalho — antes de commitar, ao encerrar a sessão, ou ao pedir explicitamente para atualizar a memória — execute esta rotina de debrief.

## Quando usar

Esta skill se aplica quando o usuário diz coisas como:
- "vou commitar"
- "atualize a memória"
- "atualize o STATE"
- "feche a sessão"
- "vamos fazer o debrief"
- "antes de subir, atualize a documentação"

Também se aplica proativamente quando você terminou uma unidade coerente de trabalho (uma feature, um refactor, uma correção de bug não-trivial) e o usuário ainda não pediu explicitamente. Nesse caso, sugira o debrief antes de propor commit.

## Procedimento

Execute os passos em ordem. Cada passo é condicional ao que mudou na sessão.

### 1. Examine o que foi feito

Rode `git status` e `git diff --staged` (ou `git diff HEAD` se não há staging). Identifique:
- Quais arquivos foram modificados, adicionados, ou removidos
- Quais features do Manifest foram tocadas (cruze com `.agent-memory/manifest/features/F-*.md::contracts`)
- Se houve mudança de comportamento observável (não apenas refactor mecânico)

### 2. Atualize entradas do Manifest

Para cada feature cujo código foi tocado:
- Atualize `metrics` se houver medição nova (com `last_measured` ISO timestamp)
- Atualize `version` se a release mudou
- Adicione, modifique ou remova entradas em `acceptance` se o comportamento mudou
- Atualize `status` se a feature transitou (`planned` → `in_progress` → `shipped` → `deprecated`)

Se uma capacidade nova foi adicionada e não tem entrada no Manifest, **crie uma**:
- ID monotônico (próximo número disponível em `.agent-memory/manifest/features/`)
- `status: in_progress` se ainda não está completa, `shipped` se está
- Critérios de aceitação em notação EARS (ver seção "Notação EARS" abaixo)

### 3. Grave um checkpoint

A partir de F-0015 (ADR-0018), `STATE.md` é view derivada de checkpoints append-only — você nunca o reescreve diretamente. Em vez disso, invoque:

```bash
agent-memory checkpoint \
  --summary "resumo da sessão (1-3 frases)" \
  --current "estado real agora, em uma frase" \
  --next "próxima ação concreta, em uma frase" \
  --features F-NNNN,F-NNNN \
  --decisions ADR-NNNN \
  --blocked-on "se houver bloqueio externo (ou omita)" \
  --author claude-opus-4.7
```

Flags omitidas herdam do checkpoint anterior (continuidade trivial). O comando anexa um arquivo imutável em `.agent-memory/checkpoints/YYYY-MM-DD-HHMMSS.md` e regera `STATE.md` automaticamente — `Current`, `Next`, `active_*`, `blocked_on` são derivados do último checkpoint; a tabela `Recent` é gerada a partir dos 5 anteriores. Reescritas destrutivas tornam-se impossíveis por construção.

Em projetos pré-v0.6 sem `.agent-memory/checkpoints/`, rode `agent-memory migrate --to=checkpoints` uma vez para criar o checkpoint inicial a partir do `STATE.md` legado (idempotente, não-destrutivo).

Se o STATE.md ficou inconsistente por edição manual indevida, `agent-memory state-rebuild` regera sem criar novo checkpoint (recovery).

### 4. Decida sobre ADR

Se a sessão produziu uma decisão arquitetural não-trivial:
- Rode `agent-memory propose-adr --staged` para gerar um draft em `.agent-memory/decisions/proposals/`
- Examine o draft, complete as seções TODO (Contexto, Decisão, Consequências, Alternativas rejeitadas)
- Quando completo, mova de `.agent-memory/decisions/proposals/NNNN-draft.md` para `.agent-memory/decisions/NNNN-slug-final.md`
- Atualize `affects_features` no frontmatter do ADR para listar features impactadas

Regra prática: se um futuro contribuidor olhando o commit em seis meses precisaria de explicação para entender a escolha, é ADR. Se a explicação cabe na mensagem de commit, não é.

Não force criação de ADR para refactors mecânicos, renames, ou correções de bug óbvias.

### 5. Valide

Rode `agent-memory audit --strict --no-index` antes de propor o commit. Se o pre-commit hook está instalado, ele vai rodar isso automaticamente — mas validar antes evita falha tardia.

Se a auditoria reportar drift, examine: ou um caminho em `contracts` virou inválido (precisa atualizar a feature), ou um arquivo foi removido sem deprecar a feature correspondente.

Se a sessão atual está em uma branch que será mesclada de volta para uma branch principal (geralmente `main` ou `develop`), rode adicionalmente `agent-memory audit --check-collisions origin/main` para detectar colisões de IDs antes do merge. A checagem compara os IDs novos criados nesta branch com os IDs existentes na branch destino, e avisa se duas branches paralelas criaram features ou ADRs com o mesmo ID. Se há colisão, renumere o artefato local antes do commit, atualizando o nome do arquivo, o campo `id` no frontmatter, e qualquer referência cruzada. ADRs já mesclados na branch destino nunca são renumerados — apenas o que está chegando se ajusta.

### 6. Apresente o resumo

Antes de fazer o commit (ou pedir ao usuário para fazê-lo), mostre:
- Arquivos do Manifest atualizados ou criados (com IDs)
- Como o STATE.md ficou (Current e Next)
- Status do ADR, se aplicável (proposto em `.agent-memory/decisions/proposals/` ou finalizado em `.agent-memory/decisions/`)
- Resultado da auditoria (compliance, drift, cobertura)

### 7. Registre adesão na telemetria local

Após o resumo, invoque (silencioso, falha não bloqueia):

```bash
agent-memory record debrief_run features=F-NNNN,F-NNNN
```

Substitua pela lista de IDs efetivamente tocados nesta sessão. A telemetria é local-only (`.agent-memory/.telemetry.jsonl`, gitignored) e opt-out via `.meta.yaml::telemetry_enabled=false` — F-0014, ADR-0017. O sinal alimenta `agent-memory log --summary` para o mantenedor verificar adesão.

## Notação EARS

Critérios de aceitação no Manifest seguem a notação EARS. Cada critério tem `id`, `pattern`, e os campos exigidos pelo padrão escolhido:

- **`ubiquitous`** (sempre ativo): `requirement`
  Use para invariantes do sistema. Exemplo: "O sistema deve manter embeddings L2-normalizados".

- **`event`** (gatilho externo): `trigger`, `response`
  Use para estímulo-resposta. Exemplo: trigger "endpoint recebe query com k > 0", response "retorna top-k por cosine".

- **`state`** (em determinada condição): `state`, `response`
  Use para comportamento condicional ao estado interno. Exemplo: state "índice em reindexação", response "retorna HTTP 503".

- **`optional`** (feature opcional ativa): `feature`, `response`
  Use para flags ou parâmetros opcionais. Exemplo: feature "metric=dot_product fornecido", response "usa dot product".

- **`unwanted`** (situação indesejada): `trigger`, `response`
  Use para condições de erro e proteções defensivas. Exemplo: trigger "vetor de magnitude zero", response "retorna HTTP 400".

- **`complex`** (combinações): `requirement`
  Escape para combinações que não cabem nos cinco padrões básicos. Use com parcimônia — quebrar em múltiplos critérios simples geralmente é preferível.

## O que evitar

Não invente features apenas para preencher o Manifest. Se a mudança não introduz ou modifica capacidade nomeável, não precisa entrar.

Não pule a atualização do STATE.md mesmo quando parece pequena. O STATE é o cursor da próxima sessão, e perder uma atualização força o próximo agente a reconstruir contexto a partir do código.

Não promova drafts de ADR (`.agent-memory/decisions/proposals/`) para `.agent-memory/decisions/` sem revisão humana. Se você é o próprio agente preenchendo o draft, está apenas redigindo — a aprovação para mover para `.agent-memory/decisions/` deve vir do usuário.

Não force criação de ADR para mudanças mecânicas (rename de variável, fix de typo, ajuste de imports, refactor sem mudança comportamental).

Não atualize `metrics` no Manifest com valores inventados. Se não há medição real desta sessão, mantenha os valores anteriores ou remova o campo.
