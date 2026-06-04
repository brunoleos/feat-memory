---
schema_version: 2
project: nome-do-projeto
stack:
  language: python>=3.10
  architecture: hexagonal
  primary_db: postgres
constraints:
  - id: C1
    severity: hard
    rule: "Pydantic obrigatório para schemas de borda"
  - id: C2
    severity: hard
    rule: "Nenhuma PII em logs externos"
  - id: C3
    severity: soft
    rule: "Docstrings obrigatórias em funções públicas"
references:
  manifest_index: ./.agent-memory/manifest/INDEX.md
  state: ./.agent-memory/STATE.md
  decisions_index: ./.agent-memory/decisions/INDEX.md
  methodology: https://github.com/brunoleos/agent-memory/blob/v{VERSION}/METHODOLOGY.md
  skills: ./skills/
budgets:
  resumption_max_bytes: 12288
  state_max_bytes: 4096
---

# Constituição do projeto

<!-- Espaço para seções específicas do projeto, escritas pelo mantenedor
humano se e quando achar útil: ## Identidade, ## Restrições não-negociáveis,
## Convenções de código, etc. O agent-memory nunca escreve essas seções —
adicione-as e mantenha-as fora do bloco delimitado abaixo. -->

<!-- >>> agent-memory >>> -->
## agent-memory

Sessões começam por `.agent-memory/STATE.md` (foco atual) e `.agent-memory/manifest/INDEX.md` (mapa de capacidades). Detalhes de uma feature ficam em `.agent-memory/manifest/features/F-NNNN-*.md`. Decisões arquiteturais em `.agent-memory/decisions/`. A metodologia completa está documentada no repositório do agent-memory: <https://github.com/brunoleos/agent-memory/blob/v{VERSION}/METHODOLOGY.md>.

Este bloco é refrescado a cada `agent-memory deploy`. Não edite diretamente — mudanças aqui são sobrescritas no próximo redeploy. Conteúdo específico do projeto vai fora das marcações HTML que delimitam este bloco.

### Skills disponíveis

Quatro skills em `skills/` orientam os fluxos críticos. Leia o `SKILL.md` de cada uma antes de executá-la — o frontmatter traz os triggers de ativação e as instruções autoritativas (fonte única; não duplicadas aqui). Roster:

- **`memory-deploy`** — instalar/adotar a metodologia num projeto: deploy mecânico e, em legacy, gênese retroativa multi-fonte (testes, telas, código, deps; git secundário).
- **`memory-bootstrap`** — retomar uma sessão: carregar o contexto e dar o briefing tático ("onde paramos", "qual o status").
- **`memory-debrief`** — fechar/commitar uma sessão: atualizar Manifest e STATE e propor ADR a partir do diff. A mais usada no dia-a-dia.
- **`memory-pull-brief`** — após `git pull`, brifar o que veio do remote e ressincronizar o STATE.

### Como retomar trabalho

A constituição é carregada automaticamente. Em seguida, você deve carregar `.agent-memory/STATE.md` para descobrir o foco da sessão e os IDs de features e decisões ativas. Apenas as features e ADRs listados em `STATE.md::active_features` e `STATE.md::active_decisions` precisam ser expandidos no contexto inicial — carregar o Manifest inteiro ou todos os ADRs viola o orçamento de retomada.
<!-- <<< agent-memory <<< -->
