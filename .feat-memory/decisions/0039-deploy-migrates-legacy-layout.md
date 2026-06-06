---
id: ADR-0039
date: 2026-06-06
status: accepted
version: 1.3.0
supersedes: null
superseded_by: null
affects_features: [F-0034]
related: [ADR-0036, ADR-0008, ADR-0013]
tags: [deploy, migration, legacy, upgrade, breaking-change, dogfooding]
---

# ADR-0039 · deploy migra o layout legado `.agent-memory/` → `.feat-memory/`

## Contexto

O rename hard (ADR-0036) é breaking para quem já adotou a metodologia: a CLI lê
caminhos `.feat-memory/` fixos, então um projeto consumidor com `.agent-memory/` para
de funcionar até renomear o diretório. Sem um caminho de upgrade automático, cada
consumidor teria de descobrir e fazer a migração à mão — exatamente o atrito que a
ferramenta existe para remover. A própria transição deste repo mostrou os passos
não-óbvios: além de renomear o diretório, é preciso reinstalar o pre-commit hook (que
passou a chamar `feat-memory`) e remover o pacote pipx antigo `agent-memory`.

## Decisão

O `deploy` — o comando que consumidores já rodam para instalar/atualizar — passa a
**auto-migrar** o layout legado no início do fluxo, via `migrate_legacy_layout`:

- Se existe `.agent-memory/` e **não** existe `.feat-memory/`: renomeia o diretório
  (`Path.rename`, preserva conteúdo). Em seguida o próprio deploy reinstala o hook e
  refresca o bloco em `AGENTS.md`, completando a transição.
- **Não-destrutivo:** se `.agent-memory/` e `.feat-memory/` coexistem, não sobrescreve
  — avisa e deixa o legado para reconciliação manual.
- **Idempotente:** sem `.agent-memory/`, é no-op.
- Remove o transiente legado `.agent-memory-deploy/`.
- Emite avisos acionáveis: reinstalação do hook e `pipx uninstall agent-memory`.

Decisão acessória (sem ADR próprio, é refino de heurística): `.claude/` entra nos
prefixos **não-código** do gate (`STALENESS_NONCODE_PREFIXES`). Specs de subagent
(F-0033) são conteúdo de metodologia, não produto — não devem disparar o gate
doc-sync sozinhas. O deploy também avisa o consumidor a versionar `.claude/agents/`
quando `.claude/` está no `.gitignore` (regra de exclusão de pai do Git impede um fix
automático confiável).

## Consequências

Positivas: upgrade de um comando (`feat-memory deploy`) para quem vinha de
`agent-memory`; transição segura (não clobbera dados) e idempotente. Dogfood: este
repo passa a versionar seu `.claude/agents/` (gitignore ajustado para `.claude/*` +
`!.claude/agents/`).

Negativas: a migração só cobre o **rename de diretório** — referências textuais ao
nome antigo na prosa dos artefatos do consumidor não são reescritas (cosmético, não
afeta a CLI). Aceito: reescrever conteúdo do consumidor automaticamente seria
invasivo; o deploy refresca só o que gerencia (bloco AGENTS.md, meta).

## Alternativas rejeitadas

- **Subcomando dedicado (`migrate --to feat-layout`):** mais um comando a descobrir;
  o upgrade natural é rodar `deploy`, então a migração mora lá, automática.
- **Reescrever todo o conteúdo do consumidor (como neste repo):** invasivo sobre
  arquivos que não são nossos; o necessário para funcionar é só o rename do diretório.
- **Fixar o `.gitignore` do consumidor para `.claude/agents/` automaticamente:** a
  regra de exclusão de diretório-pai do Git torna isso não-confiável; um aviso é honesto.
