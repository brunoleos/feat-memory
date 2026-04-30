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
  manifest_index: ./manifest/INDEX.md
  state: ./STATE.md
  decisions_index: ./decisions/INDEX.md
  methodology: https://github.com/brunoleos/agent-memory/blob/v{VERSION}/METHODOLOGY.md
  skills: ./skills/
budgets:
  resumption_max_bytes: 12288
  state_max_bytes: 4096
  feature_file_max_bytes: 6144
---

# Constituição do projeto

Sessões começam por `STATE.md` (foco atual) e `manifest/INDEX.md` (mapa de capacidades). Detalhes de uma feature ficam em `manifest/features/F-NNNN-*.md`. Decisões arquiteturais em `decisions/`. A metodologia completa está documentada no repositório do agent-memory: <https://github.com/brunoleos/agent-memory/blob/v{VERSION}/METHODOLOGY.md>.

<!--
Personalização: durante o setup inicial, a skill `memory-deploy` insere
seções específicas do projeto entre este comentário e `## Skills disponíveis`:

  ## Identidade
  ## Restrições não-negociáveis
  ## Convenções de código

Remova este comentário após a personalização.
-->

## Skills disponíveis

Este projeto inclui três skills em `skills/` (na raiz do workspace) que orientam você nos fluxos críticos da metodologia. Cada skill tem um arquivo `SKILL.md` com instruções detalhadas e condições de ativação no frontmatter. Use-as quando os triggers correspondentes aparecerem na conversa, lendo o `SKILL.md` correspondente antes de executar — as skills são autoritativas sobre como cada fluxo deve ser conduzido.

A skill `memory-deploy` é o ponto de entrada único para instalar a metodologia em qualquer projeto. Ela ativa quando o usuário pede para instalar, configurar ou adotar a metodologia, com frases como "instale a metodologia neste projeto", "configure o agent-memory aqui" ou "este projeto não tem AGENT.md". Ela detecta automaticamente se o projeto é greenfield (novo, pouco código, poucos commits) ou legacy (com história e código de produção), executa o `agent-memory deploy` para a estrutura mecânica, e conduz personalização interativa ou gênese retroativa em quatro fases conforme o caso. Esta skill só é invocada na adoção inicial — depois disso, o projeto está instalado e as outras duas skills cobrem o uso diário.

A skill `memory-bootstrap` ativa no início de uma sessão quando o usuário pergunta sobre o estado atual do projeto, com frases como "onde paramos", "qual o status" ou "carregue o contexto". Ela carrega os artefatos de memória eficientemente e apresenta um briefing tático antes de você prosseguir com a tarefa.

A skill `memory-debrief` ativa quando o usuário sinaliza intenção de commitar ou fechar a sessão, com frases como "vou commitar", "atualize o STATE" ou "antes de subir". Ela executa a rotina de debrief: examina o diff, atualiza entradas do Manifest para features tocadas, reescreve o `STATE.md`, e gera proposta de ADR se a sessão produziu uma decisão arquitetural não-trivial. Esta é a skill mais importante do dia-a-dia — invoque-a antes de cada commit relevante.

## Como retomar trabalho

A constituição é carregada automaticamente. Em seguida, você deve carregar `STATE.md` para descobrir o foco da sessão e os IDs de features e decisões ativas. Apenas as features e ADRs listados em `STATE.md::active_features` e `STATE.md::active_decisions` precisam ser expandidos no contexto inicial — carregar o Manifest inteiro ou todos os ADRs viola o orçamento de retomada.
