---
id: ADR-0018
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0015]
related: [ADR-0009, ADR-0014]
tags: [state, checkpoint, model, retomada, dogfooding]
---

# ADR-0018 · STATE.md como view derivada de checkpoints append-only

## Contexto

`STATE.md` hoje é editado em-place pela skill `memory-debrief`. Cada sessão reescreve as seções `Current`, `Next`, `Recent`, `active_features`, `active_decisions`, `blocked_on`. Funciona, mas tem três problemas dolorosos quando a sessão é longa ou intercalada com pausa:

1. **Reescrita destrói contexto silenciosamente.** Se o agente reescreve `Current` com uma frase que perde a nuance da última sessão, a perda é irreversível — não há histórico de "o que estava lá antes". A skill `memory-bootstrap` na próxima retomada lê só a versão pobre, e o foco real fica enterrado em git log.
2. **`Recent` é editado à mão.** Buffer circular de 5 linhas, agente é responsável por adicionar nova e remover mais antiga. Toda vez que o ritual de debrief é apressado, `Recent` fica desatualizado ou incoerente. Foi exatamente o sintoma listado em FUTURE_IMPROVEMENTS.md como motivação para esta feature.
3. **"O que mudou no foco essa semana?" exige `git log -p STATE.md`.** Pergunta legítima e frequente, resposta cara. O dado da evolução do foco existe (no histórico do arquivo), mas exige intermediação manual.

A reflexão sobre essas três frições aponta para uma inversão de modelo: **STATE.md deixa de ser fonte da verdade e vira view derivada**. Cada sessão grava um checkpoint imutável; `STATE.md` é regenerado a partir dos últimos N checkpoints como conveniência para `memory-bootstrap` (que segue lendo o mesmo arquivo, mesmo schema). É o mesmo padrão de event sourcing: append-only events + materialized view.

ADR-0009 (apply methodology to self) já estabeleceu o C3. Esta decisão é uma aplicação direta: o histórico do foco ganha o mesmo tratamento que o histórico de decisões — append-only, indexado, recuperável.

## Decisão

Cada invocação de `memory-debrief` (ou manual via `agent-memory checkpoint`) cria um arquivo novo em `.agent-memory/checkpoints/YYYY-MM-DD-HHMMSS.md` com frontmatter contendo o snapshot do foco e corpo de notas livres. Os arquivos são imutáveis após gravação — agentes nunca editam um checkpoint existente, apenas anexam novos.

`STATE.md` é regenerado por `agent-memory checkpoint` (após anexar) e por `agent-memory state-rebuild` (recovery sem novo checkpoint). O formato preservado é o atual:

- Frontmatter (`schema_version`, `updated_at`, `updated_by`, `active_features`, `active_decisions`, `blocked_on`)
- Sections `## Current`, `## Next`, `## Recent`

Mas o conteúdo é derivado:

- `updated_at` = `ts` do checkpoint mais recente.
- `updated_by` = `author` do checkpoint mais recente.
- `active_features`, `active_decisions`, `blocked_on` = campos do checkpoint mais recente.
- `Current` = `current` do checkpoint mais recente.
- `Next` = `next` do checkpoint mais recente.
- `Recent` = tabela com os últimos 5 checkpoints (anteriores ao atual), cada linha = `ts | author | features tocadas | summary`.

A janela de "view" é configurável via `.agent-memory/.meta.yaml::state_view_window` (default `1` para `Current`/`Next`/`active_*`). Exposição como dial dá controle ao mantenedor que prefere ver os 3 últimos foco em `Current` (ex: projetos com sessões muito curtas que se sucedem).

`memory-bootstrap` continua lendo `STATE.md` exatamente como antes — o contrato a montante é preservado. A skill não sabe que o conteúdo é gerado. Isso é o ponto: é Liskov-safe.

`memory-debrief` muda: passo "reescrever STATE.md" vira "invocar `agent-memory checkpoint --summary '...'`" com flags opcionais para `--features`, `--decisions`, `--blocked-on`, `--current`, `--next`. A skill nunca toca diretamente `STATE.md`.

A migração de consumidores existentes é tratada por `agent-memory migrate --to=checkpoints` (formalizado em ADR-0019): lê o `STATE.md` atual e escreve um checkpoint inicial derivado dele, marcando o `author` como `migration`. Após isso, `STATE.md` é regerado a partir desse primeiro checkpoint — o conteúdo permanece equivalente, e o histórico passa a acumular.

## Consequências

**Positivas**:

- Reescrita destrutiva torna-se impossível por construção: cada checkpoint é um arquivo novo, o anterior fica intocado. Auditoria do drift de foco vira `ls .agent-memory/checkpoints/`.
- "O que mudou no foco essa semana?" vira `agent-memory log` da telemetria + glob dos checkpoints filtrados por data. Não precisa `git log -p`.
- O `Recent` em STATE.md fica sempre atual e coerente, derivado dos checkpoints anteriores. Buffer circular vira algoritmo, não disciplina.
- Recoverável: se um agente regenera STATE.md mal (improvável, mas), `agent-memory state-rebuild` fica como vassoura.
- Schema do STATE.md inalterado: `memory-bootstrap`, audit cross-check, e qualquer ferramenta externa que parseie STATE.md continuam funcionando sem mudança. Custo de adoção ≈ zero para quem só lê.
- Telemetria F-0014 ganha sinal natural: cada checkpoint é uma evidência de debrief executado. `agent-memory log --summary` correlaciona checkpoint count com debrief count.
- O modelo encoraja sessões curtas e bem-debriefadas porque cada checkpoint é registro permanente. Disciplina por design.

**Negativas**:

- Pasta `.agent-memory/checkpoints/` cresce com a vida do projeto. Mitigação esperada: rotação ou compactação (TODO horizonte; não bloqueia v0.6). Em projetos com 1 checkpoint/dia, ~365 arquivos por ano — manejável.
- Migração de projetos existentes exige um comando dedicado. Mitigação: `migrate --to=checkpoints` é idempotente (detecta migração já feita) e a skill `memory-debrief` pode invocá-lo automaticamente se detectar `checkpoints/` vazio.
- `STATE.md` aparece como modificado em diff toda vez que um checkpoint é gravado, mesmo que só o timestamp mudou. Aceito — é refletindo trabalho real, e `merge=ours` em `.gitattributes` (já configurado) tolera o churn.
- Mais arquivos para o agente entender. Mitigação: a skill `memory-debrief` esconde a complexidade — só os comandos novos importam para o usuário. `memory-bootstrap` não muda.

## Alternativas rejeitadas

**Manter edição em-place de STATE.md, adicionar versionamento via Git**. Solução de menor esforço, mas não resolve nenhum dos três problemas. Reescrita continua destrutiva ao nível semântico (mesmo com git, perdeu-se nuance se a frase nova não diz a mesma coisa). `Recent` continua disciplinar. "O que mudou na semana" continua via `git log`. Rejeitada por não atacar a causa raiz.

**Eventos via JSONL (como F-0014 telemetry)**. Mais simples mecanicamente, mas perde a riqueza do markdown corporal. Checkpoints têm body de notas livres em prosa — agente registra raciocínio, descobertas, links. JSONL forçaria estrutura e perderia o canal natural de "minhas anotações daquela sessão". Rejeitada por força tipológica errada.

**STATE.md fonte da verdade + skill que cria backup automático antes de reescrever**. Resolveria problema 1 mecanicamente. Mas backups são obscuros, e nem `Recent` nem agregabilidade de "essa semana" ficam mais fáceis. Rejeitada como meia-medida.

**Janela de view fixa em 1, sem configuração**. YAGNI inverso: a janela é pedida explicitamente porque alguns projetos com sessões muito curtas vão querer ver mais de um. Aceito o pequeno custo de configuração para não trancar a porta. Rejeitada como inflexibilidade prematura.

**Permitir edição manual de checkpoints**. Tentador (correção de typo no summary). Rejeitada porque corrompe o modelo (checkpoints não-imutáveis perdem garantia de histórico fiel) e a correção é facilmente feita criando um checkpoint novo logo a seguir. Disciplina vs ergonomia: disciplina vence aqui.
