---
id: F-0013
name: hook-staleness-staged
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: >
  Avisa (sem bloquear) quando um commit toca código sem atualizar
  STATE.md, no momento exato do commit. Captura a degradação mais
  comum da metodologia (esquecer de invocar /memory-debrief) onde
  a intervenção é mais barata. Reusa a heurística de "código" de
  F-0011 para coerência entre os dois sinais.
contracts:
  api:
    - src/agent_memory/check_staleness.py::run
    - src/agent_memory/check_staleness.py::staged_warning
    - src/agent_memory/data/hooks/pre-commit
  tests:
    - tests/test_check_staleness.py
acceptance:
  - id: A1
    pattern: event
    trigger: "`agent-memory check-staleness-staged` é invocado e o staging contém algum path 'código' sem incluir .agent-memory/STATE.md"
    response: >
      emite na stderr uma linha amarela (ANSI quando isatty)
      sugerindo /memory-debrief, e sai com 0 (soft, nunca bloqueia)
  - id: A2
    pattern: state
    state: "o staging inclui .agent-memory/STATE.md"
    response: >
      `check-staleness-staged` sai com 0 sem emitir aviso, mesmo que
      também haja paths de código no staging
  - id: A3
    pattern: state
    state: "o staging contém apenas paths não-código (.agent-memory/, tests/, docs/, README.md, etc.)"
    response: >
      `check-staleness-staged` sai com 0 sem emitir aviso
  - id: A4
    pattern: ubiquitous
    requirement: >
      o exit code é sempre 0 — soft sempre, nunca bloqueia o commit;
      o sinal vive na stderr para ser visto pelo dev/agente, não para
      ser tratado como retry
  - id: A5
    pattern: event
    trigger: "o pre-commit hook é executado"
    response: >
      após `agent-memory audit --strict --no-index`, invoca
      `agent-memory check-staleness-staged` independentemente do
      returncode do audit (o aviso é informativo, não condicional)
  - id: A6
    pattern: unwanted
    trigger: "`git diff --cached` falha (não-Git ou erro inesperado)"
    response: >
      `check-staleness-staged` retorna sem emitir aviso (fail-soft);
      ausência de staging não deve mascarar como "tudo ok"
depends_on: [F-0005, F-0011]
decisions: [ADR-0016]
---

# F-0013 · hook-staleness-staged

## Comportamento

Adiciona um sinal informativo ao pre-commit hook capturando o cenário onde o commit toca código mas STATE.md não foi atualizado — sintoma direto de `/memory-debrief` esquecido.

**Subcomando.** `agent-memory check-staleness-staged` em [src/agent_memory/check_staleness.py](src/agent_memory/check_staleness.py). Lê `git diff --cached --name-only`, classifica cada path com `_is_code_path` (importado de [audit.py](src/agent_memory/audit.py) — mesma heurística que `--check-staleness` de F-0011). Se há paths de código E `.agent-memory/STATE.md` não está no staging, imprime na stderr:

```
⚠ agent-memory: commit toca código sem atualizar STATE.md — considere /memory-debrief
```

Cor amarela (ANSI) quando `stderr.isatty()`; plain em CI. Sempre exit 0.

**Hook.** [src/agent_memory/data/hooks/pre-commit](src/agent_memory/data/hooks/pre-commit) ganha invocação adicional após o audit existente. Roda independentemente do returncode do audit (o aviso é informativo, não bloqueio condicional). O hook continua propagando o exit code do audit para falhas hard.

**Reuso de F-0011.** Constantes `STALENESS_NONCODE_PREFIXES` e `STALENESS_NONCODE_EXACT` e função `_is_code_path` vivem em audit.py. Esta feature importa de lá — uma única definição de "código" para os dois sinais (history-side em F-0011, staged-side em F-0013).
