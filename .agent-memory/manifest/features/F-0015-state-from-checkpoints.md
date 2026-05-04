---
id: F-0015
name: state-from-checkpoints
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: >
  Inverte STATE.md de fonte da verdade para view derivada, eliminando
  a possibilidade de reescrita destrutiva por debriefs apressados.
  Cada sessão grava um checkpoint imutável; STATE.md é regerado a
  partir dos N últimos. memory-bootstrap continua lendo o mesmo
  arquivo, mesmo schema (Liskov-safe). "O que mudou no foco essa
  semana?" vira `ls .agent-memory/checkpoints/` em vez de `git log`.
contracts:
  api:
    - src/agent_memory/checkpoints.py::run_checkpoint
    - src/agent_memory/checkpoints.py::run_state_rebuild
    - src/agent_memory/checkpoints.py::render_state
    - src/agent_memory/checkpoints.py::append_checkpoint
    - src/agent_memory/migrate.py::run
  tests:
    - tests/test_checkpoints.py
acceptance:
  - id: A1
    pattern: event
    trigger: "`agent-memory checkpoint --summary 'X' --current 'Y' --next 'Z'` é invocado"
    response: >
      cria `.agent-memory/checkpoints/YYYY-MM-DD-HHMMSS.md` com o
      frontmatter especificado em ADR-0019, e regera `STATE.md`
      como view do checkpoint mais recente
  - id: A2
    pattern: ubiquitous
    requirement: >
      checkpoints existentes nunca são modificados — `agent-memory
      checkpoint` sempre cria arquivo novo; em colisão de timestamp
      sufixa com `-N` incremental
  - id: A3
    pattern: state
    state: "há ao menos um checkpoint em .agent-memory/checkpoints/"
    response: >
      `STATE.md` é gerado com Current/Next vindos do mais recente,
      Recent como tabela dos N anteriores (default 5),
      `active_features`/`active_decisions`/`blocked_on` espelhando
      o último checkpoint
  - id: A4
    pattern: event
    trigger: "`agent-memory state-rebuild` é invocado"
    response: >
      regera `STATE.md` a partir dos checkpoints existentes sem
      criar novo checkpoint (recovery)
  - id: A5
    pattern: event
    trigger: "`agent-memory migrate --to=checkpoints` é invocado e checkpoints/ está vazio"
    response: >
      lê o `STATE.md` atual, extrai Current/Next/active_*/blocked_on
      e cria um checkpoint inicial com `author=migration`; preserva
      o body do STATE.md (incluindo tabela Recent legada) no corpo
      do checkpoint; regera STATE.md
  - id: A6
    pattern: state
    state: "checkpoints/ já tem arquivos"
    response: >
      `agent-memory migrate --to=checkpoints` é idempotente — emite
      mensagem informativa e retorna 0 sem tocar nada
  - id: A7
    pattern: optional
    feature: ".agent-memory/.meta.yaml::state_view_window for definido"
    response: >
      o renderer usa N=state_view_window para selecionar quantos
      checkpoints alimentam Current/Next (default N=1, A3 vale
      para o caso default)
  - id: A8
    pattern: ubiquitous
    requirement: >
      a skill `memory-debrief` invoca `agent-memory checkpoint`
      em vez de reescrever `STATE.md` diretamente; o contrato com
      `memory-bootstrap` (lê STATE.md, mesmo schema) é preservado
depends_on: [F-0008, F-0014]
decisions: [ADR-0018, ADR-0019]
---

# F-0015 · state-from-checkpoints

## Comportamento

Inverte o modelo de `STATE.md`: deixa de ser fonte da verdade editada em-place, vira view derivada de checkpoints append-only em `.agent-memory/checkpoints/`. ADR-0018 explica o porquê; ADR-0019 fixa o schema dos arquivos e o caminho de migração.

**Comandos novos.** Implementados em [src/agent_memory/checkpoints.py](src/agent_memory/checkpoints.py):

- `agent-memory checkpoint --summary "..." [--current ...] [--next ...] [--features ...] [--decisions ...] [--blocked-on ...] [--author ...]`: anexa novo checkpoint e regera STATE.md.
- `agent-memory state-rebuild`: regera STATE.md sem criar checkpoint (recovery).
- `agent-memory migrate --to=checkpoints`: cria primeiro checkpoint a partir do STATE.md legado.

**Schema de checkpoint.** Frontmatter obrigatório: `schema_version`, `ts`, `author`, `current`, `next`, `summary`. Opcionais: `active_features`, `active_decisions`, `blocked_on`. Corpo é livre — notas, raciocínio, links. Filename `YYYY-MM-DD-HHMMSS.md` (UTC, sortable lex = sortable temporal); colisão resolvida com sufixo `-N`.

**Renderer.** `render_state(checkpoints, window)` produz o STATE.md mantendo schema atual (`schema_version: 2`, mesmas seções `Current`/`Next`/`Recent`, mesmo frontmatter). `memory-bootstrap` continua lendo do mesmo lugar — Liskov-safe.

**Janela.** Default 1 (Current/Next vêm do último). `Recent` mostra os 5 anteriores. Configurável via `.meta.yaml::state_view_window`.

**Skill atualizada.** [skills/memory-debrief/SKILL.md](skills/memory-debrief/SKILL.md) passo 3 passa a invocar `agent-memory checkpoint --summary '...'` em vez de reescrever STATE.md diretamente. Reescritas destrutivas tornam-se impossíveis por construção.

**Migração.** [src/agent_memory/migrate.py](src/agent_memory/migrate.py) ganha modo `--to=checkpoints`. Não-destrutivo (não apaga STATE.md), idempotente (detecta migração já feita).

**Audit.** [src/agent_memory/audit.py](src/agent_memory/audit.py) `validate_state` segue validando shape do frontmatter; nenhuma mudança de contrato (STATE.md gerado tem mesmo shape do STATE.md autorado).

**Deploy.** [src/agent_memory/deploy.py](src/agent_memory/deploy.py) cria `.agent-memory/checkpoints/.gitkeep` na inicialização.
