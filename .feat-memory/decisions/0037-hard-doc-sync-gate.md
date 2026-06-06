---
id: ADR-0037
date: 2026-06-06
status: accepted
version: 1.1.0
supersedes: null
superseded_by: null
affects_features: [F-0032]
related: [ADR-0008, ADR-0016, ADR-0020]
tags: [hooks, governance, enforcement, drift, dogfooding]
---

# ADR-0037 · gate hard de sincronização doc↔código no commit

## Contexto

A promessa central do `feat-memory` é que a documentação de features e decisões
acompanha o código. Até aqui isso era **disciplina assistida**, não garantia: o
único sinal no commit que olhava "código mudou, e a doc?" era o
`check-staleness-staged` (F-0013, ADR-0016) — deliberadamente **soft** (sempre exit
0) e restrito a `STATE.md`. Um nudge que se podia ignorar. Resultado: nada impedia
um commit de código sem nenhum movimento no Manifest/decisões/STATE; o drift só
aparecia no audit retroativo.

O hook já tem precedente de guard **hard** dentro de uma estrutura fail-open:
`check-version-bump-staged` (ADR-0020) bloqueia código sem bump de VERSION, mas o
hook como um todo continua fail-open quando o binário não está no PATH (ADR-0008).
A garantia de sincronia doc↔código cabe na mesma forma.

## Decisão

Novo subcomando **`check-doc-sync-staged`** (hard, exit 1), ligado ao pre-commit
hook. Bloqueia o commit quando há **código staged** (mesma heurística `_is_code_path`
do staleness — `.feat-memory/`, `tests/`, `docs/` e alguns nomes exatos *não* são
código) **sem que nenhum artefato de doc esteja staged**. "Artefato de doc" =
qualquer um de `.feat-memory/STATE.md`, `.feat-memory/manifest/**` ou
`.feat-memory/decisions/**`.

Relação com ADR-0016 (não o supersede):
- O **soft** `check-staleness-staged` permanece: nudga especificamente para o STATE
  ("considere /memory-debrief"), sempre exit 0.
- O **hard** `check-doc-sync-staged` garante que *algum* artefato de doc se moveu —
  é mais amplo (STATE **ou** manifest **ou** decisions) mas bloqueia.

Os dois se complementam: o hard fecha a porta do drift; o soft aponta a direção
preferida. A fail-open de binário-ausente (ADR-0008) é preservada — quem não tem a
CLI no PATH ainda commita, com aviso. Contornável deliberadamente com
`git commit --no-verify`.

## Consequências

Positivas: a sincronização doc↔código vira **garantia mecânica** no boundary de
commit, não disciplina — exatamente o diferencial que o reposicionamento (ADR-0036)
quer cravar. Aceitar manifest/decisions além de STATE evita falso-bloqueio quando a
sessão registrou uma decisão/feature sem mexer no STATE.

Negativas: commits que legitimamente só tocam código (raro neste fluxo) passam a
exigir `--no-verify` ou um toque de doc; aceito — é o ponto do gate. O guard não
julga *qualidade* da doc (se o update é relevante), só *presença* — coerente com
ADR-0028 (enforça o que é barato e confiável; não finge medir o que não dá).

## Alternativas rejeitadas

- **Promover o staleness-check (ADR-0016) de soft a hard:** acoplaria o bloqueio a
  `STATE.md` especificamente, falso-bloqueando quem registrou só uma feature/ADR. O
  gate certo é "alguma doc se moveu", não "o STATE se moveu".
- **Flag `--strict` no `check-staleness-staged` em vez de subcomando novo:**
  misturaria dois contratos (soft-STATE e hard-doc-sync) num só comando; separá-los
  mantém cada um testável e com semântica única.
- **Bloquear via `audit --strict` apenas:** o audit olha o estado dos artefatos, não
  o *staging* do commit; não distingue "código sem doc neste commit".
