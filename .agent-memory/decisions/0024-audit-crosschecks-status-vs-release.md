---
id: ADR-0024
date: 2026-06-03
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0020]
related: [ADR-0014, ADR-0008, ADR-0016]
tags: [audit, governance, validation, dogfooding, anti-drift]
---

# ADR-0024 · audit confronta status de feature contra releases reais

## Contexto

A auditoria deste próprio repo passou clean com 11 features `in_progress` que já
tinham saído nas releases v0.6.0–v0.9.0, e com o STATE 23 dias velho. O controle
existente valida **validade estrutural** (schema via F-0002, integridade
referencial de IDs via F-0011/ADR-0014) mas não **verdade semântica**: nada
confronta o `status` declarado com o que de fato foi released. O campo `status` é
digitado à mão e ninguém o checa contra a realidade do versionamento.

O único sinal que pegaria o STATE velho — `--check-staleness` — é opt-in e ficava
desligado por padrão; o `agent-memory audit` interativo mostrava `Frescor: 551 h`
como número neutro, sem destaque. Defesa desligada por padrão é defesa que não
existe. Foi assim que o projeto que existe para impedir memória-mentirosa
acumulou, ele mesmo, memória mentirosa.

## Decisão

O `audit` ganha duas frentes anti-drift, em níveis de coerção deliberadamente
distintos:

1. **Release-status cross-check (`validate_release_status`) — Issue/warning,
   default-on.** Feature com `status: in_progress` cujo `version` consta como
   released é drift. "Released" = união de seções datadas `## [X.Y.Z]` do
   `CHANGELOG.md` com tags Git `vX.Y.Z` (`released_versions`, fail-soft). Emite
   warning. Sendo Issue, o pre-commit hook (`audit --strict`) o **promove a error
   e bloqueia o commit** — correto: commitar uma feature já-released ainda marcada
   in_progress deve falhar. Tolerante a `version` ausente e a ausência de
   CHANGELOG/tags (não inventa sinal).

2. **Frescor do STATE em destaque — apresentação, NÃO Issue.** Acima de
   `STALENESS_WARN_HOURS` (14 dias), `print_report` marca o frescor com aviso
   visual. **Deliberadamente não vira Issue.** Staleness no momento do commit já é
   coberta, soft e fail-open, por F-0013 (`check-staleness-staged`, ADR-0016).
   Promover staleness a Issue faria o `audit --strict` do hook bloquear commits
   por STATE velho — transformaria um nudge em coerção dura para todos os
   consumidores. O destaque visual resolve a causa real ("o número estava à vista
   mas não sinalizado") sem esse efeito colateral.

A assimetria é o ponto: drift de *status já released* é mentira factual e merece
bloqueio sob strict; STATE *velho* é higiene e merece nudge. ADR-0008 (fail-open
do hook) preservado para o segundo, justificadamente fortalecido para o primeiro.

## Alternativas rejeitadas

- **Staleness default-on como Issue:** sob o `audit --strict` do pre-commit
  bloquearia commit por STATE velho — coerção que leva a desinstalar o hook.
  Rejeitada em favor do destaque de apresentação.
- **Derivar "released" só do arquivo VERSION:** ambíguo — uma feature com
  `version == VERSION` atual pode ser tanto recém-released quanto em-progresso
  para a próxima. CHANGELOG/tags datam o que de fato saiu.
- **Marcar shipped automaticamente quando detecta release:** audit não deve mutar
  artefatos de memória (só índices); reescrever status é decisão do debrief
  humano/agente. Audit sinaliza, não corrige.
- **Hard error em vez de warning para o cross-check:** warning + promoção por
  strict dá o mesmo bloqueio no commit sem quebrar quem roda `audit` interativo
  só para inspecionar.
