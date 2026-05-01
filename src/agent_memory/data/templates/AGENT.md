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
  feature_file_max_bytes: 6144
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

Este projeto inclui quatro skills em `skills/` (na raiz do workspace) que orientam você nos fluxos críticos da metodologia. Cada skill tem um arquivo `SKILL.md` com instruções detalhadas e condições de ativação no frontmatter. Use-as quando os triggers correspondentes aparecerem na conversa, lendo o `SKILL.md` correspondente antes de executar — as skills são autoritativas sobre como cada fluxo deve ser conduzido.

A skill `memory-deploy` é o ponto de entrada único para instalar a metodologia em qualquer projeto. Ela ativa quando o usuário pede para instalar, configurar ou adotar a metodologia, com frases como "instale a metodologia neste projeto", "configure o agent-memory aqui" ou "este projeto não tem AGENT.md". Ela detecta se o projeto é greenfield ou legacy, executa `agent-memory deploy` para instalar a estrutura mecânica, e em projetos legacy conduz gênese retroativa de ADRs (a partir do git log) e do Manifest (a partir dos entrypoints públicos). A skill nunca escreve no corpo da `AGENT.md` fora do bloco delimitado por sentinelas — identidade, restrições e convenções específicas do projeto são autoria do mantenedor humano.

A skill `memory-bootstrap` ativa no início de uma sessão quando o usuário pergunta sobre o estado atual do projeto, com frases como "onde paramos", "qual o status" ou "carregue o contexto". Ela carrega os artefatos de memória eficientemente e apresenta um briefing tático antes de você prosseguir com a tarefa. Quando detecta que o último commit é um merge que tocou artefatos da metodologia, ela delega para `memory-pull-brief` antes do briefing tático.

A skill `memory-debrief` ativa quando o usuário sinaliza intenção de commitar ou fechar a sessão, com frases como "vou commitar", "atualize o STATE" ou "antes de subir". Ela executa a rotina de debrief: examina o diff, atualiza entradas do Manifest para features tocadas, reescreve o `STATE.md`, e gera proposta de ADR se a sessão produziu uma decisão arquitetural não-trivial. Esta é a skill mais importante do dia-a-dia — invoque-a antes de cada commit relevante.

A skill `memory-pull-brief` ativa após `git pull` quando o usuário pergunta o que veio do remote, com frases como "o que veio do pull", "brifa as mudanças do main" ou "ressincroniza o STATE com o que veio". Ela examina o diff trazido pelo pull, identifica mudanças em features, decisions e no bloco metodológico de AGENT.md, e propõe ajustes em `STATE.md` para refletir a nova realidade — sem tocar `manifest/` nem `decisions/`, que já vieram corretos do pull.

### Como retomar trabalho

A constituição é carregada automaticamente. Em seguida, você deve carregar `.agent-memory/STATE.md` para descobrir o foco da sessão e os IDs de features e decisões ativas. Apenas as features e ADRs listados em `STATE.md::active_features` e `STATE.md::active_decisions` precisam ser expandidos no contexto inicial — carregar o Manifest inteiro ou todos os ADRs viola o orçamento de retomada.
<!-- <<< agent-memory <<< -->
