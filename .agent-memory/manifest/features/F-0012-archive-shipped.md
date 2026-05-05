---
id: F-0012
name: archive-shipped
status: in_progress
introduced: 2026-05-04
version: 0.6.0
user_value: >
  Reduz o orçamento de retomada movendo features shipped (e fora de
  active_features) para `manifest/archive/`, mantendo discoverability
  via um INDEX próprio e preservando histórico via `git mv`. ADRs
  nunca são arquivados (são registro histórico imutável). Default é
  dry-run para evitar movimentação acidental.
contracts:
  api:
    - src/agent_memory/memory/archive.py::run
    - src/agent_memory/memory/archive.py::collect_eligible
    - src/agent_memory/governance/audit.py::run_audit
    - src/agent_memory/governance/audit.py::gen_archive_index
  tests:
    - tests/test_archive.py
acceptance:
  - id: A1
    pattern: event
    trigger: "`agent-memory archive` é invocado sem flags"
    response: >
      lista as features elegíveis em formato legível (id, nome, motivo)
      e sai com 0 sem mover arquivo nenhum (default dry-run)
  - id: A2
    pattern: event
    trigger: "`agent-memory archive --apply` é invocado"
    response: >
      move cada arquivo elegível de `manifest/features/` para
      `manifest/archive/` (via `git mv` quando em repo Git, fallback
      `shutil.move`), regenera ambos os INDEXes e sai com 0
  - id: A3
    pattern: state
    state: "uma feature tem status='shipped' E está em STATE.md::active_features"
    response: >
      a feature NÃO é elegível ao arquivamento (active vence shipped);
      permanece em `manifest/features/` mesmo que fosse selecionada por
      status sozinho
  - id: A4
    pattern: ubiquitous
    requirement: >
      `audit.run_audit` valida schema e detecta drift de contracts
      em features tanto de `manifest/features/` quanto de
      `manifest/archive/`; gera dois INDEXes separados (um por diretório)
  - id: A5
    pattern: ubiquitous
    requirement: >
      ADRs nunca são arquivados pelo subcomando — não há flag para isso
      e o módulo `archive.py` não toca em `decisions/`
  - id: A6
    pattern: unwanted
    trigger: "`git mv` falha (ex: arquivo não-tracked)"
    response: >
      cai para `shutil.move` e prossegue; o usuário fica responsável
      por `git add` posterior se quiser versionar a movimentação
depends_on: [F-0002, F-0011]
decisions: [ADR-0015]
---

# F-0012 · archive-shipped

## Comportamento

Subcomando `agent-memory archive` move features `shipped` (e fora de `active_features`) para `.agent-memory/manifest/archive/`, reduzindo o tamanho do INDEX que `memory-bootstrap` carrega na retomada.

**Default dry-run.** Sem flags, lista o que seria arquivado e sai com 0. Para mover de fato, `--apply`. Inverte a convenção habitual (default = ação) deliberadamente — ADR-0015 explica: o custo de "esqueci o flag" é zero, o de "movi sem querer" é commit indesejado.

**Critério.** `status == "shipped"` E `id ∉ STATE.md::active_features`. As duas condições devem se manter; basta uma falhar para a feature ficar.

**Movimento.** Tenta `git mv` primeiro (preserva blame); fallback `shutil.move` se falhar (projetos sem Git, arquivos não-tracked). Após mover, regenera `manifest/INDEX.md` e `manifest/archive/INDEX.md` chamando `gen_manifest_index` e `gen_archive_index` em [audit.py](src/agent_memory/governance/audit.py).

**Audit consciente do archive.** `run_audit` ganha varredura adicional de `manifest/archive/F-*.md` para validação de schema e drift de contracts. Cross-check de F-0011 já procura em ambos. INDEXes são gerados separadamente.

ADRs nunca são arquivados — registro histórico imutável por design (`superseded_by` cobre a semântica de "não use mais"). O subcomando não tem opção para isso.
