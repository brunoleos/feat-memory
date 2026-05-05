---
id: F-0016
name: check-version-bump
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: >
  Bloqueia commits que tocam código sem atualizar VERSION, garantindo
  que a versão visível ao consumidor (`__version__`, `.meta.yaml::version`,
  eventos de telemetria) seja honesta. Exceção deliberada à política
  fail-open de ADR-0008 — soft tornaria a versão mentirosa silenciosa,
  o que nenhuma feature dependente (F-0010, F-0014, F-0018) tolera.
  Auto opt-in: no-op em projetos sem arquivo VERSION na raiz.
contracts:
  api:
    - src/agent_memory/check_version_bump.py::needs_bump
    - src/agent_memory/check_version_bump.py::run
    - src/agent_memory/data/hooks/pre-commit
  tests:
    - tests/test_check_version_bump.py
acceptance:
  - id: A1
    pattern: event
    trigger: "`agent-memory check-version-bump-staged` é invocado e o staging contém algum path 'código' sem incluir VERSION"
    response: >
      emite na stderr (vermelha quando isatty) mensagem de erro
      explicando bump SemVer e como contornar com --no-verify;
      sai com 1 (bloqueia commit)
  - id: A2
    pattern: state
    state: "o staging inclui VERSION"
    response: >
      `check-version-bump-staged` sai com 0 sem emitir mensagem,
      mesmo que também haja paths de código no staging
  - id: A3
    pattern: state
    state: "o staging contém apenas paths não-código (.agent-memory/, tests/, docs/, README.md, etc.)"
    response: >
      `check-version-bump-staged` sai com 0 sem emitir mensagem
      (não há código mudando, não precisa bumpar)
  - id: A4
    pattern: unwanted
    trigger: "o arquivo `VERSION` não existe na raiz do projeto"
    response: >
      `check-version-bump-staged` sai com 0 sem emitir mensagem
      (auto opt-in: sem VERSION, sem guard); zero-config para
      projetos que não adotam SemVer estrito
  - id: A5
    pattern: event
    trigger: "o pre-commit hook é executado"
    response: >
      após `agent-memory audit` e `agent-memory check-staleness-staged`,
      invoca `agent-memory check-version-bump-staged`; o exit code do
      hook é o `or` do exit code do audit e deste check (qualquer um
      falhando bloqueia)
  - id: A6
    pattern: unwanted
    trigger: "`git diff --cached` falha (não-Git ou erro inesperado)"
    response: >
      `check-version-bump-staged` retorna 0 sem emitir mensagem
      (fail-soft em ambientes degradados)
  - id: A7
    pattern: ubiquitous
    requirement: >
      a heurística de "código" é importada de `audit._is_code_path`
      (F-0011) — uma única definição compartilhada entre os três
      sinais (audit --check-staleness, check-staleness-staged,
      check-version-bump-staged)
depends_on: [F-0005, F-0011]
decisions: [ADR-0020]
---

# F-0016 · check-version-bump

## Comportamento

Adiciona um guard hard ao pre-commit hook capturando o cenário onde o commit toca código mas `VERSION` não foi atualizado — sintoma direto de release sem bump.

**Subcomando.** `agent-memory check-version-bump-staged` em [src/agent_memory/check_version_bump.py](src/agent_memory/check_version_bump.py). Lê `git diff --cached --name-only`, classifica cada path com `_is_code_path` (importado de [audit.py](src/agent_memory/audit.py)). Se há paths de código E `VERSION` não está no staging, imprime na stderr (vermelho ANSI quando `isatty`):

```
agent-memory: commit toca código mas VERSION não foi atualizado.
  Bump conforme SemVer:
    - patch (0.0.X) para correção pequena
    - minor (0.X.0) para nova feature
    - major (X.0.0) para breaking change na API
  Para contornar: git commit --no-verify
```

Sai com exit 1 (bloqueia o commit).

**Auto opt-in.** Se `VERSION` não existe na raiz, é no-op (exit 0). Projetos que ainda não adotam SemVer estrito não pagam custo. Para ativar, basta criar o arquivo `VERSION` na raiz.

**Hook.** [src/agent_memory/data/hooks/pre-commit](src/agent_memory/data/hooks/pre-commit) ganha invocação após o `check-staleness-staged` existente (F-0013). Propaga via `result.returncode or bump_check.returncode` — qualquer um falhando bloqueia.

**Reuso de F-0011.** Constantes `STALENESS_NONCODE_PREFIXES` e `STALENESS_NONCODE_EXACT` e função `_is_code_path` vivem em audit.py. Esta feature importa de lá — uma única definição de "código" para os três sinais (history-side em F-0011, staged-side em F-0013, version-bump-side em F-0016).

**Exceção a ADR-0008.** Este é o primeiro check **hard** no hook (audit já era hard, mas por validação de schema; este é hard por política de release). ADR-0020 documenta o porquê: soft treinaria a ignorar, e versão mentirosa quebra F-0010/F-0014/F-0018 silenciosamente. Bypass deliberado via `--no-verify` cobre WIP.
