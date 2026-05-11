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

# ADR-0009 · Aplicar a metodologia ao próprio projeto (dogfooding)

## Contexto

A metodologia foi desenvolvida entre v0.1.0 e v0.3.0 sem ser aplicada ao seu próprio desenvolvimento. Feedback ficava indireto (via consumidores externos) e a credibilidade sofre — "se nem o autor aplica, por que eu deveria?".

## Decisão

Aplicar agent-memory ao próprio repositório via gênese retroativa conduzida pela skill `memory-deploy`. A gênese inicial produziu: AGENTS.md com 4 constraints `hard`; 8 ADRs cobrindo fundações de schema e evolução da instalação; 8 features no Manifest; STATE.md inicial. A constraint `C3` (hard) formaliza a obrigação contínua. Custo: atrito adicional no fluxo (cada PR não-trivial atualiza Manifest e potencialmente registra ADR). Risco real é drift entre código e Manifest — paradoxalmente o problema que a metodologia se propõe a resolver; mitigado por `--strict` no hook e CI.

## Alternativas rejeitadas

- **Não fazer dogfooding**: feedback indireto, tool pode evoluir em direções que parecem boas no papel mas falham na prática.
- **Dogfooding incremental**: adoção parcial gera dívida indefinida sobre quando completar.
- **Greenfield (descartar histórico)**: apaga proveniência real (evolução de instalação v0.1.0 → v0.3.0); preservada como ADRs.
