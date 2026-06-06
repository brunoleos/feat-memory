---
id: ADR-0036
date: 2026-06-06
status: accepted
version: 1.0.0
supersedes: null
superseded_by: null
affects_features: []
related: [ADR-0007, ADR-0009, ADR-0021]
tags: [naming, positioning, methodology, breaking-change, dogfooding]
---

# ADR-0036 · rename para `feat-memory` + reposicionamento

## Contexto

Duas forças convergiram:

1. **A memória de agente virou commodity nativa.** O Claude Code passou a embarcar
   uma memória persistente por agente em `.claude/agent-memory/<name>/`, indexada por
   um `MEMORY.md` — um scratchpad fino, sem schema nem governança. Isso (a) valida a
   tese de que memória durável de agente importa, mas (b) **comoditiza** justamente a
   leitura rasa do que este projeto fazia, e (c) **colide nominalmente**: a feature
   nativa se chama literalmente `agent-memory` e usa `.claude/agent-memory/`, enquanto
   este projeto se chamava `agent-memory` e usava `.agent-memory/`.

2. **O nome subdimensionava o valor.** O diferencial real nunca foi "ter um diretório
   de memória", e sim a **camada de governança que mantém a documentação de features e
   decisões viva e sempre sincronizada com o código** (audit, constraints enforced,
   trilha de ADRs, gate no commit). "memory" descrevia o sintoma, não a capacidade.

## Decisão

**Hard rename, sem camada de compatibilidade** (viável porque ainda não houve release
na PyPI):

- pacote import `agent_memory` → `feat_memory`;
- distribuição + comando CLI `agent-memory` → `feat-memory`;
- diretório de artefatos `.agent-memory/` → `.feat-memory/` (e `.agent-memory-deploy/`
  → `.feat-memory-deploy/`).

O novo nome lê como **"feature memory"** — memória de *features e decisões* —, que é o
que os quatro artefatos efetivamente são. Resolve a colisão com a feature homônima do
Claude Code e realinha a identidade ao valor (governança de doc viva).

A reescrita foi **uniforme em todo o repositório, inclusive nos ADRs históricos e
features arquivadas** (decisão explícita do mantenedor): troca-se a fidelidade literal
ao nome de época pela consistência nominal total. O diretório foi movido com `git mv`
(preserva histórico); equivalência comportamental provada pela suíte (215 testes
verdes) e por `audit --strict` limpo (schema 1.00, drift 0, constraints C1/C2 ok).

**Versão 1.0.0:** o reposicionamento é o marco de maturidade da metodologia e assume
compromisso de estabilidade da superfície (CLI/artefatos) daqui em diante.

## Consequências

Positivas: nome alinhado ao valor; colisão com a memória nativa resolvida; o `1.0`
sinaliza maturidade e dá um ponto de estabilidade para consumidores. A memória nativa
do Claude Code passa a **coexistir** (sem integração) — `feat-memory` é a camada
governada por cima, não um substituto do scratchpad.

Negativas: breaking total para qualquer consumidor pré-existente (import, comando e
diretório mudam) — exige migração de layout (`.agent-memory/` → `.feat-memory/`),
capacidade a entregar à parte. Os ADRs históricos perderam a fidelidade literal ao
nome da época — aceito conscientemente em troca de consistência.

Ação externa requerida do mantenedor (fora do código): reservar `feat-memory` na PyPI
(+ trusted publisher) e renomear o repositório GitHub `brunoleos/agent-memory` →
`brunoleos/feat-memory` para que os links versionados resolvam.

## Alternativas rejeitadas

- **Manter `agent-memory` + alias de comando:** preserva a colisão nominal e o
  subdimensionamento; um meio-termo que não resolve o problema de posicionamento.
- **Preservar a prosa dos ADRs históricos (não reescrever):** mais fiel à imutabilidade
  de ADR, mas deixaria o nome antigo espalhado pelo registro; o mantenedor preferiu
  consistência nominal completa.
- **Bump 0.16.0 em vez de 1.0.0:** trataria um reposicionamento de identidade como
  mais um incremento; não marcaria o ponto de maturidade/estabilidade.
