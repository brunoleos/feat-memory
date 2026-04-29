---
id: ADR-0009
date: 2026-04-29
version: v0.3.0
status: accepted
supersedes: null
superseded_by: null
affects_features: []
related: []
tags: [meta, dogfooding, methodology]
---

# ADR-0009 · Aplicar a metodologia agent-memory ao próprio projeto (dogfooding)

## Contexto

A metodologia agent-memory foi desenvolvida como projeto Python independente entre v0.1.0 e v0.3.0 sem que ela própria fosse aplicada ao seu desenvolvimento. Isso criava um descompasso entre o que a tool prega (gestão de memória persistente para agentes LLM) e como ela é desenvolvida (sem essa gestão). O risco é validar a metodologia apenas através do feedback de outros projetos consumidores, sem o ciclo de feedback mais curto possível: o próprio time experimentando os atritos e benefícios diretamente.

Adicionalmente, a credibilidade da metodologia sofre quando o próprio criador não a usa — "se nem o autor da tool aplica, por que eu deveria?" é uma pergunta legítima que potenciais adotantes fazem.

## Decisão

Aplicar agent-memory ao próprio repositório agent-memory via gênese retroativa em quatro fases conduzida pela skill `memory-deploy`. A gênese inicial produziu: AGENT.md personalizado com 4 constraints `hard`; 8 ADRs cobrindo as fundações de schema da metodologia (multi-agent, hard/soft, EARS, três skills) e a evolução de instalação (.agent-memory/ versionado → gitignored → pacote pipx); 8 features no Manifest cobrindo os 4 subcomandos CLI, o pre-commit hook e as 3 skills; STATE.md inicial.

A constraint `C3` (hard) em AGENT.md formaliza a obrigação contínua: "O projeto segue a metodologia agent-memory para gestão de agentes LLM." Mudanças de capacidade da tool agora exigem update do Manifest no mesmo commit; decisões arquiteturais não-triviais exigem ADR; sessões fecham com debrief antes do commit.

## Consequências

Feedback curto e direto sobre os atritos da metodologia — quando algo é ergonomicamente ruim, o próprio time sente primeiro. Exemplo vivo para consumidores: o repositório do agent-memory passa a demonstrar a metodologia em uso, não apenas descrevê-la. Pressão construtiva para resolver problemas que outros projetos podem estar enfrentando silenciosamente (e.g., a falta do campo `version` no schema de ADR foi descoberta na própria gênese e está documentada como débito em FUTURE_IMPROVEMENTS).

Custo: atrito adicional no fluxo de desenvolvimento da tool — cada PR não-trivial agora exige atualizar Manifest e potencialmente registrar ADR. Risco real: mudanças na tool podem não acompanhar mudanças no próprio uso (drift entre código e Manifest), o que paradoxalmente é o problema que a metodologia se propõe a resolver. Mitigação: pre-commit hook em modo `--strict` detecta drift; CI deve rodar `agent-memory audit --strict` como segunda linha.

## Alternativas rejeitadas

Não fazer dogfooding (manter o status quo) foi rejeitado porque o feedback ficou indireto e a credibilidade da metodologia sofre. Sem aplicação ao próprio projeto, a tool corre o risco de evoluir em direções que parecem boas no papel mas falham na prática.

Dogfooding incremental (aplicar só a algumas partes ou só a partir de um certo ponto no histórico) foi rejeitado porque adoção parcial gera dívida indefinida sobre quando completar. Ou se aplica a metodologia toda — incluindo gênese retroativa para reconstruir o histórico de decisões — ou ela perde força como demonstração. A skill `memory-deploy` no fluxo legacy foi desenhada precisamente para tornar essa adoção retroativa viável em uma sessão.

Aplicar via fluxo greenfield (descartar histórico e começar do zero) foi rejeitado porque o histórico Git existente contém decisões reais já tomadas (a evolução de instalação v0.1.0 → v0.3.0, em particular) que merecem ser preservadas como ADRs. Greenfield apagaria essa proveniência.
