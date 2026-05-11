---
id: ADR-0020
date: 2026-05-04
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0016]
related: [ADR-0008, ADR-0014, ADR-0016]
tags: [hooks, semver, release, fail-open-exception]
---

# ADR-0020 · Pre-commit hook bloqueia (hard) commits que tocam código sem bumpar VERSION

## Contexto

F-0013 endereçou o caso soft (commit toca código sem atualizar STATE.md). O caso simétrico é mais arriscado: commit toca código sem bumpar `VERSION` — releases sem bump fazem `pipx upgrade` entregar código novo com mesma versão visível, `.meta.yaml` fica congelado, telemetria F-0014 anota eventos diferentes com mesma versão (indistinguíveis), F-0018 não consegue detectar drift. Sinal aqui é determinístico (código novo ⇒ exige bump), diferente do binário-ausente que ADR-0008 cobriu. Justifica exceção a fail-open **se** existe bypass deliberado fácil — `--no-verify` cobre WIP.

## Decisão

Subcomando `agent-memory check-version-bump-staged` invocado pelo hook após `check-staleness-staged`. Lê `git diff --cached --name-only`; sem path "código" → exit 0. Com código E `VERSION` ausente do staging → exit 1 com stderr vermelha explicando bump SemVer e bypass via `--no-verify`. **`VERSION` arquivo inexistente na raiz → no-op (exit 0)** — auto opt-in: projetos sem SemVer estrito não pagam custo. Hook propaga via `result.returncode or bump_check.returncode` (qualquer um falhando bloqueia; audit toma precedência semântica na mensagem). Heurística de "código" compartilhada com F-0011/F-0013 — uma definição vale para os três.

## Alternativas rejeitadas

- **Manter soft (warning, exit 0)**: treinaria a ignorar; versão mentirosa silenciosa é exatamente o que F-0010/F-0014/F-0018 não toleram.
- **Validar conteúdo de VERSION (parser SemVer)**: complexidade significativa (pre-releases, build metadata, política patch vs minor); 95% dos casos cobertos por staging check.
- **Configurável via `.meta.yaml::version_bump_required`**: superfície sem caso real; auto opt-in via existência de `VERSION` já segmenta.
- **Só na CI, não no hook**: hook captura cedo (dev reage no momento); CI captura tarde.
- **Bloquear só em main/master**: agente em qualquer branch pode esquecer; `--no-verify` cobre WIP; branch-aware é elegância sem ganho.
