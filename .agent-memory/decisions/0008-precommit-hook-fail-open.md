---
id: ADR-0008
date: 2026-04-29
version: v0.3.0
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0005]
related: []
tags: [hooks, audit, ux]
---

# ADR-0008 · Pre-commit hook chama `agent-memory audit` direto; fail-open quando ausente do PATH

## Contexto

Com a CLI no PATH (ADR-0007), o hook pode chamar `agent-memory audit --strict` direto em vez de procurar `audit.py` em paths fixos. Surge a sub-pergunta: o que fazer quando o binário não está no PATH (dev sem `pipx install`, CI sem a tool)?

## Decisão

Hook chama `agent-memory audit --strict --no-index` direto. Binário ausente: warning com instruções de instalação, libera o commit (**fail-open**). Binário presente e audit falha: bloqueia normalmente. `git commit --no-verify` continua disponível para casos excepcionais. Princípio: hooks que falham por estado do ambiente acabam desinstalados (`rm .git/hooks/pre-commit`); hook desinstalado não protege ninguém. Custo: em CI o fail-open mascara o problema; mitigação é a CI rodar `agent-memory audit --strict` explicitamente como step separado, sem confiar no hook como rede de segurança.

## Alternativas rejeitadas

- **Bloquear quando binário ausente**: gera bypass habitual via `--no-verify` ou desinstalação do hook; hábito destruído > nudge perdido.
- **Hook procurando `audit.py` em paths fixos**: frágil; qualquer reorganização interna quebra. Chamar CLI no PATH desacopla.
