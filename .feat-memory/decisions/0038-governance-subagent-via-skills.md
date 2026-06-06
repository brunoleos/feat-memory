---
id: ADR-0038
date: 2026-06-06
status: accepted
version: 1.2.0
supersedes: null
superseded_by: null
affects_features: [F-0033]
related: [ADR-0004, ADR-0036, ADR-0021]
tags: [subagent, skill, deploy, claude-code, adapter, methodology]
---

# ADR-0038 · subagent de governança via campo `skills:` (fonte única na skill)

## Contexto

O `memory-debrief` é uma **skill**: roda no contexto principal e *hidrata* a sessão
(é esse o ponto — o humano e o agente principal veem o resultado). Mas o trabalho do
debrief — ler o diff staged inteiro, o STATE, o Manifest e as decisões para então
gerar a atualização — **inunda o contexto principal** com leituras que não serão
referenciadas depois. Esse é exatamente o caso de uso de um subagent do Claude Code:
fazer o trabalho pesado numa janela isolada e devolver só o resumo.

O risco óbvio de "criar um subagent de debrief" é **duplicar a lógica** que já vive na
skill: dois prompts que divergem com o tempo. O Claude Code oferece a saída: o campo
`skills:` do frontmatter de subagent **pré-carrega o conteúdo da skill** no contexto do
subagent na partida.

## Decisão

Distribuir um subagent `.claude/agents/memory-debrief.md` — um **wrapper fino** cujo
frontmatter declara `skills: [memory-debrief]`. A **skill permanece a fonte única** da
lógica; o subagent só adiciona (a) a janela isolada e (b) as regras de operação:
escrever em `.feat-memory/` e **pedir confirmação ao humano antes de commitar**
(autonomia controlada — o agente não commita sozinho).

O `deploy` projeta a spec canônica (`src/feat_memory/data/agents/*.md`, novo
package-data) para `.claude/agents/` no projeto-alvo, sempre sobrescrevendo, como faz
com as skills. A spec canônica única evita divergência entre projetos.

Escopo: o subagent é um **adapter específico do Claude Code**; o núcleo da metodologia
(a skill + a CLI + os artefatos) continua tool-agnóstico via `AGENTS.md`. O subagent
escreve em `.feat-memory/` (estrutura governada), **não** na memória nativa do Claude
Code — esta apenas coexiste, sem integração.

## Consequências

Positivas: o debrief ganha contexto isolado (não polui a conversa principal) **sem
duplicar lógica** — a skill é a única fonte, o subagent é casca. O `deploy` entrega o
adapter pronto; o dogfood (C3) usa o próprio subagent. "Pede confirmação antes de
commitar" mantém o humano no loop.

Negativas: introduz um artefato Claude-Code-specific (`.claude/agents/`) no que era
100% tool-agnóstico — aceito por ser **adapter opcional fora do núcleo**, não o
mecanismo principal. Outras ferramentas (Cursor/Kilo) ficam sem o subagent até que se
escreva um adapter equivalente (fora de escopo; Movimento de interop segue descopado).

## Alternativas rejeitadas

- **Subagent com o prompt da skill copiado:** duplica a lógica; os dois divergem. O
  campo `skills:` existe justamente para evitar isso.
- **Converter a skill em subagent (em vez de wrapper):** perderia o uso da skill no
  contexto principal, que é desejável para bootstrap/pull-brief e para o próprio
  debrief quando o humano quer ver o processo. As três outras skills (ADR-0004)
  continuam só-skill.
- **Subagent com `memory:` nativo apontando para `.feat-memory/`:** acoplaria a
  estrutura governada ao mecanismo nativo; a decisão do mantenedor foi coexistir sem
  integração — o subagent escreve direto nos artefatos.
