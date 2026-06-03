---
id: ADR-0026
date: 2026-06-03
status: accepted
version: 0.11.0
supersedes: null
superseded_by: null
affects_features: [F-0022]
related: [ADR-0008, ADR-0014, ADR-0024]
tags: [ci, audit, portability, constraints, dogfooding]
---

# ADR-0026 · CI cross-OS como segunda linha de defesa

## Contexto

Duas lacunas de enforcement coexistiam:

1. **C1 declarada mas nunca testada.** A constraint hard C1 afirma que a tool "roda
   em Linux, macOS e Windows nativamente". Isso nunca foi *verificado* — a suíte só
   roda na máquina do mantenedor (Windows). Uma regressão de portabilidade (path
   separators, encoding, `subprocess`) passaria despercebida.

2. **Pre-commit é pulável.** O hook (ADR-0008) roda `audit --strict`, mas
   `git commit --no-verify` o ignora — por design (fail-open evita que hooks
   coercitivos sejam desinstalados). Sem uma segunda linha, um commit que pulou o
   hook chega ao `main` sem auditoria.

## Decisão

`.github/workflows/ci.yml` roda em `push` (main) e `pull_request`:

- **Matriz `os × python`** = {ubuntu, macos, windows} × {3.11, 3.12}. Torna C1
  **verificável por execução**, não por declaração — o espírito de F-0011/F-0020
  (auditar verdade, não forma) aplicado à própria portabilidade.
- Passos: `pip install -e .[dev]` → `pytest -q` → `agent-memory audit --strict
  --json`. O audit no CI é a segunda linha de defesa para commits que pularam o
  hook. Limiar de bloqueio: qualquer issue (error, ou warning sob `--strict`).
- Sem shell script (C1): só comandos diretos no YAML.

## Alternativas rejeitadas

- **Rodar só em ubuntu:** mais barato, mas não testa C1 — o ponto inteiro.
  macOS/Windows são onde bugs de path/encoding aparecem.
- **CI sem `audit`, só pytest:** perderia a segunda linha de defesa; o pre-commit
  pulável ficaria sem rede de segurança.
- **`audit` sem `--strict` no CI:** deixaria drift (warnings) passar; a CI é o lugar
  certo para ser estrita, já que não tem o custo interativo do dev.
