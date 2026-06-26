---
id: ADR-0018
date: 2026-05-04
status: superseded
supersedes: null
superseded_by: ADR-0043
affects_features: [F-0015]
related: [ADR-0009, ADR-0014]
tags: [state, checkpoint, model, retomada, dogfooding]
---

# ADR-0018 · STATE.md como view derivada de checkpoints append-only

## Contexto

`STATE.md` era editado em-place pela skill `memory-debrief` — três problemas: (1) reescrita destrói contexto silenciosamente (nuance perdida fica irrecuperável); (2) `Recent` é buffer circular editado à mão, desatualiza quando o ritual é apressado; (3) "o que mudou no foco essa semana?" exige `git log -p STATE.md`. A inversão natural: STATE.md vira view derivada; cada sessão grava checkpoint imutável. Mesmo padrão de event sourcing.

## Decisão

Cada `memory-debrief` (ou manual via `feat-memory checkpoint`) cria arquivo novo em `.feat-memory/checkpoints/YYYY-MM-DD-HHMMSS.md` com frontmatter do snapshot e corpo de notas livres. Arquivos imutáveis — agentes nunca editam um existente. `STATE.md` é regenerado por `feat-memory checkpoint` (após anexar) e por `state-rebuild` (recovery). Mantém shape atual; conteúdo derivado: `Current`/`Next`/`active_*`/`blocked_on` do checkpoint mais recente, `Recent` dos 5 anteriores. Janela configurável via `.meta.yaml::state_view_window` (default 1). `memory-bootstrap` lê o mesmo arquivo, mesmo schema — Liskov-safe. ADR-0019 detalha schema do checkpoint e migração. Telemetria F-0014 ganha sinal natural (cada checkpoint = evidência de debrief).

## Alternativas rejeitadas

- **Manter edição em-place + versionamento via Git**: não resolve nenhum problema; reescrita continua destrutiva ao nível semântico, `Recent` continua disciplinar.
- **Eventos via JSONL** (como F-0014): perde a riqueza do markdown corporal; checkpoints têm body de notas/raciocínio em prosa.
- **STATE.md como fonte + backup automático**: backups são obscuros, e nem `Recent` nem agregabilidade ficam mais fáceis.
- **Janela fixa em 1, sem configuração**: alguns projetos com sessões curtas vão querer ver mais; custo de configuração mínimo.
- **Permitir edição manual de checkpoints**: corrompe o modelo; correção é trivial via novo checkpoint.
