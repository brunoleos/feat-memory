---
id: ADR-0033
date: 2026-06-04
status: accepted
version: 0.14.0
supersedes: null
superseded_by: null
affects_features: [F-0029]
related: [ADR-0021]
tags: [cli, ux, paths, consistency]
---

# ADR-0033 · todos os subcomandos aceitam `[path]` opcional (default cwd)

## Contexto

Os subcomandos tinham três convenções de path diferentes:

- `deploy <target>` — posicional **obrigatório**.
- `audit` — sem posicional; resolve o root via `git rev-parse`/cwd
  (`paths._init_paths()`).
- `migrate` — sem posicional; **falhava** com "unrecognized arguments" se você passasse
  um caminho.

O relatório da Tensegrara registrou: "três comandos, três convenções; isso me custou
uma rodada". Inconsistência de interface é fricção de descoberta pura — o usuário não
tem como prever, por analogia, como cada comando aceita o alvo.

## Decisão

Convenção única: **todo subcomando de projeto aceita um `[path]` posicional opcional,
com default no diretório atual.**

1. `deploy [target]` — `target` vira opcional (`nargs="?"`, default `.`).
   Retrocompatível: passar o caminho continua válido.
2. `audit [path]` e `migrate [path]` — ganham o posicional opcional.
3. **Mecanismo:** `paths._init_paths(root: Path | None = None)` passa a aceitar um
   override. Sem argumento, mantém o comportamento atual (descoberta via git/cwd); com
   `path` explícito, resolve a partir dele. Cada `run` resolve seu próprio alvo uma vez.
   `migrate --to=checkpoints` também propaga o root.

## Consequências

Positivas: interface previsível — `cmd` opera no cwd, `cmd <path>` opera no alvo, em
todos os comandos; scripts e CI podem apontar um projeto sem `cd`; remove a classe de
erro "unrecognized arguments" do migrate.

Negativas: a idempotência de `_init_paths` ganhou uma sutileza (override divergente
após o root fixado recomputa os derivados) — coberta por testes e usada uma vez por
`run`, então sem risco prático.

## Alternativas rejeitadas

- **Padronizar tudo como obrigatório (estilo `deploy`):** quebraria `audit`/`migrate`
  no fluxo comum (rodar no cwd) e seria regressão de UX.
- **Só consertar o `migrate` para não quebrar com path:** deixaria duas convenções
  ainda divergentes; a inconsistência é o problema, não só o erro do migrate.
- **Flag `--path` em vez de posicional:** mais verboso e diverge do `deploy <target>`
  já existente; o posicional opcional unifica com o que o usuário já conhece.
