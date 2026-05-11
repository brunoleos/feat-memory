---
id: ADR-0016
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0013]
related: [ADR-0008, ADR-0014]
tags: [hooks, audit, ux, fail-open]
---

# ADR-0016 · Pre-commit hook avisa (soft) sobre commits que tocam código sem atualizar STATE.md

## Contexto

O pre-commit hook de F-0005 ([data/hooks/pre-commit](src/agent_memory/data/hooks/pre-commit)) hoje executa apenas `agent-memory audit --strict --no-index`. Captura drift de schema e referências quebradas — mas é mudo sobre o pior modo de degradação da metodologia: o agente termina uma sessão de implementação, refatora código, abre o commit, e esquece de invocar `/memory-debrief`. STATE.md fica intacto enquanto o "Current"/"Next" descritos lá viraram passado. A próxima retomada lê uma narrativa obsoleta e age sobre ela.

ADR-0014 introduziu `agent-memory audit --check-staleness` que detecta esse padrão olhando o `git log` retroativamente. Útil para diagnóstico, mas chega tarde — só identifica que o agente passou a perder debriefs há dias. O ponto de intervenção mais barato é o próprio commit que vai introduzir o gap: o hook tem visibilidade do índice (`git diff --cached`) e pode comparar contra o que está sendo modificado.

A pergunta de design não é "alertar?", é "bloquear ou apenas avisar?". ADR-0008 estabeleceu o hook como fail-open quando o binário falta. A racionalidade é a mesma para sinais não-determinísticos: o agente pode legitimamente fazer um commit sem precisar tocar STATE.md (typo em comentário, ajuste de lint). Bloquear gera bypass habitual via `--no-verify`, esvaziando o sinal. Avisar mantém a visibilidade onde dói (no terminal do dev/agente, no momento exato), sem quebrar o fluxo.

## Decisão

Novo subcomando `agent-memory check-staleness-staged`, invocado pelo pre-commit hook após o audit. Lógica:

- Lê `git diff --cached --name-only` para listar paths em staging.
- Se algum path em staging for "código" (heurística de F-0011: blacklist de prefixos `.agent-memory/`, `tests/`, `docs/` mais um conjunto fixo de docs raiz como `README.md`, `CHANGELOG.md`, etc.) E `.agent-memory/STATE.md` NÃO estiver em staging, emite na stderr uma linha amarela (ANSI quando `isatty`):

  ```
  ⚠ agent-memory: commit toca código sem atualizar STATE.md — considere /memory-debrief
  ```

- Sai sempre com 0. Nunca bloqueia. O sinal vive no buffer da stderr, visível imediatamente, sem custo de retry.

O subcomando também é invocável manualmente, fora do hook, para o usuário pedir uma checagem ad-hoc do staging atual. O comportamento é idempotente.

A heurística de "código" é compartilhada com `validate_state_freshness` de F-0011 (mesmas constantes `STALENESS_NONCODE_PREFIXES` e `STALENESS_NONCODE_EXACT`). Centralizar evita drift entre os dois sinais — qualquer ajuste futuro à definição de "código" vale para ambos.

O hook continua exit-code-faithful em relação ao audit (returncode do audit propaga). O check de staleness staged roda mesmo se o audit falhou — o usuário pode estar escolhendo `--no-verify` por outro motivo, e ainda assim quer ver o aviso.

## Consequências

**Positivas**:

- O sinal chega no momento de máxima alavancagem (commit em curso). Sem espera, sem polling, sem dashboard. O dev/agente vê a linha amarela na stderr e pode pausar para debriefar antes de fazer push.
- Soft sempre: respeita ADR-0008 e evita `--no-verify` habitual. Bypass de aviso é mais difícil que bypass de erro porque não há fricção a contornar — o sinal aparece e o commit prossegue.
- Reuso direto da heurística de F-0011: uma única definição de "código" para os dois mecanismos. Mudanças futuras (ex: incluir `apps/`, `packages/` para projetos monorepo via configuração no frontmatter de AGENTS.md) propagam para ambos via mesma constante.
- Subcomando dedicado é testável e invocável avulso. O hook fica fino — só compõe `agent-memory audit` + `agent-memory check-staleness-staged`. Cada peça tem responsabilidade única.
- O exit code 0 garante que o hook não promova staleness staged a bloqueio acidental se algum dia o framework de hook do Git mudar de comportamento.

**Negativas**:

- Falsos positivos esperados. Refatoração distribuída em vários commits intermediários (atomicidade) gera o aviso em cada um, mesmo quando o debrief será feito ao fim. Aceito como custo do sinal: o aviso é barato de ignorar e não custa retry.
- Dependência de `git diff --cached`. Em workflows não-Git (raros aqui) o comando falha — fail-soft (returncode != 0 do git suprime a saída sem bloquear). Documentado.
- Aviso amarelo na stderr exige terminal que entenda ANSI; em CI capturando stdout, vai aparecer como caracteres `\033[...]`. Mitigado por checagem `isatty` antes de aplicar cor — em pipes/CI, sai plain.
- O hook continua dependente do binário `agent-memory` no PATH. Se faltar, o aviso de staleness staged também é pulado (junto com o audit). ADR-0008 já normalizou esse comportamento; este ADR não muda nada nessa frente.

## Alternativas rejeitadas

**Bloquear o commit (severity hard)**. Discutido na conversa que originou este ADR. Tentador para forçar disciplina, mas violenta o princípio fail-open de ADR-0008 e treina o usuário a usar `--no-verify` por reflexo. Quando o agente passa a sempre usar `--no-verify`, o sinal morre. Rejeitada — preferimos sinal vivo e ignorável a sinal morto e mascarado.

**Tornar o comportamento configurável via `.agent-memory/.meta.yaml::hook.staleness_severity`**. Permitiria projetos optarem por "hard" se quisessem. Adiciona superfície de configuração antes de pedido real. Aceito como TODO no horizonte: se um projeto pedir o bloqueio, expomos a flag. Por agora, soft é o único modo. Rejeitada por YAGNI.

**Detectar staleness staged dentro do `audit` em vez de subcomando separado**. Seria possível: `agent-memory audit --strict --check-staleness-staged`. Mas mistura duas semânticas — audit valida estado em repouso, staleness staged inspeciona ação em curso. Subcomando dedicado deixa claro o ponto temporal. Rejeitada por confluência inadequada.

**Embedar a lógica direto no script do hook em vez de subcomando**. Rápido, sem subprocess. Mas duplica a heurística de "código" (já viva em audit.py) e quebra a regra implícita de que o hook só compõe binários públicos da CLI. Rejeitada por acoplamento fora de lugar.

**Verificar mtime de STATE.md em vez de staging**. Não é o que importa. mtime pode ter mudado fora do contexto do commit (ex: agente leu e regravou). Staging é a verdade do que será commitado. Rejeitada por imprecisão.
