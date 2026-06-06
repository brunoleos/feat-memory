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

# ADR-0016 · Pre-commit hook avisa (soft) commits que tocam código sem atualizar STATE.md

## Contexto

ADR-0014 deu ao audit `--check-staleness` que olha o `git log` retroativamente — útil para diagnóstico mas chega tarde. O ponto de intervenção mais barato é o próprio commit que vai introduzir o gap: o hook tem `git diff --cached` e pode comparar contra o que está sendo modificado. Pergunta: bloquear ou avisar? ADR-0008 já firmou hook fail-open; mesma racionalidade vale para sinais não-determinísticos (commit pode legitimamente não exigir STATE.md — typo, lint).

## Decisão

Subcomando `feat-memory check-staleness-staged` invocado pelo hook após audit. Lê `git diff --cached --name-only`; se há path "código" (heurística importada de F-0011) E `STATE.md` não está em staging, emite stderr amarela (ANSI com `isatty`) sugerindo `/memory-debrief`. **Sai sempre com 0** — nunca bloqueia. Sinal vive no buffer da stderr, visível imediatamente, sem retry. Heurística de "código" centralizada (`STALENESS_NONCODE_PREFIXES`/`_EXACT`) — uma definição vale para F-0011, F-0013 e futuro F-0016. Hook continua exit-code-faithful em relação ao audit; staleness staged roda mesmo se audit falhou (usuário pode estar usando `--no-verify` por outro motivo).

## Alternativas rejeitadas

- **Bloquear (hard)**: viola ADR-0008 e treina `--no-verify` por reflexo, esvaziando o sinal. Soft ignorável > sinal morto.
- **Configurável via `.meta.yaml::hook.staleness_severity`**: superfície antes do pedido real; YAGNI.
- **Dentro do audit (`--check-staleness-staged`)**: mistura semânticas (audit valida repouso; staleness inspeciona ação em curso); subcomando dedicado deixa claro o ponto temporal.
- **Lógica embutida no shell do hook**: duplica heurística que já vive em audit.py.
- **Verificar mtime de STATE.md**: mtime pode mudar fora do commit; staging é a verdade do que será commitado.
