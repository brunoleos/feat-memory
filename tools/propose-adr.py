#!/usr/bin/env python3
"""
propose-adr.py — Detecta mudanças que podem merecer ADR e gera draft.

Examina o diff atual contra um commit base (HEAD~1 por padrão) e
aplica heurísticas para identificar sinais de decisão arquitetural:
volume de mudança, alterações em arquivos de dependência, padrões
em mensagens de commit. Quando detecta sinais relevantes, gera um
draft pré-preenchido em decisions/proposals/.

Drafts NÃO são ADRs — eles vivem em uma subpasta separada e são
ignorados pelo audit.py. Cabe ao humano revisar, completar as
seções TODO, renomear com slug definitivo e mover para decisions/.

Localização: .agent-memory/tools/propose-adr.py
Os artefatos ficam no project root, descoberto via git.

Uso:
    python .agent-memory/tools/propose-adr.py             # HEAD~1..HEAD
    python .agent-memory/tools/propose-adr.py --base ABC  # contra commit
    python .agent-memory/tools/propose-adr.py --staged    # mudanças staged
    python .agent-memory/tools/propose-adr.py --force     # sem sinais
    python .agent-memory/tools/propose-adr.py --prompt    # prompt LLM
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def find_project_root() -> Path:
    """Descobre o project root via git, com fallback."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "AGENT.md").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent


ROOT = find_project_root()
DECISIONS_DIR = ROOT / "decisions"
PROPOSALS_DIR = DECISIONS_DIR / "proposals"

DEPENDENCY_FILES = {
    "pyproject.toml", "requirements.txt", "Pipfile", "Pipfile.lock",
    "package.json", "package-lock.json", "yarn.lock", "tsconfig.json",
    "Cargo.toml", "Cargo.lock",
    "go.mod", "go.sum",
    "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "Gemfile.lock",
    "composer.json", "composer.lock",
    "mix.exs", "mix.lock",
}

DECISION_KEYWORDS = [
    r"\brevert(?:s|ed|ing)?\b",
    r"\binstead\s+of\b",
    r"\bswitch(?:ed)?\s+from\b",
    r"\bdecid(?:ed|e)\s+to\b",
    r"\breplac(?:ed|e)\s+\w+\s+with\b",
    r"\bmigrat(?:ed|e)\s+from\b",
    r"\bdeprecat(?:ed|e)\b",
    r"\bremov(?:ed|e)\s+\w+\s+support\b",
    r"\brefactor(?:ed)?\b",
    r"\brewrite\b",
]

THRESHOLDS = {
    "files": 5,
    "lines": 100,
}


def _run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True, cwd=ROOT)


def get_diff_stats(base: str, staged: bool) -> dict:
    args = ["diff", "--stat"]
    if staged:
        args.append("--cached")
    else:
        args.append(base)
    try:
        out = _run_git(args)
    except subprocess.CalledProcessError:
        return {"files": 0, "lines": 0}

    lines = out.strip().splitlines()
    if not lines:
        return {"files": 0, "lines": 0}

    summary = lines[-1]
    files_match = re.search(r"(\d+)\s+files?\s+changed", summary)
    ins_match = re.search(r"(\d+)\s+insertions?", summary)
    del_match = re.search(r"(\d+)\s+deletions?", summary)

    return {
        "files": int(files_match.group(1)) if files_match else 0,
        "lines": ((int(ins_match.group(1)) if ins_match else 0)
                  + (int(del_match.group(1)) if del_match else 0)),
    }


def get_changed_files(base: str, staged: bool) -> list[str]:
    args = ["diff", "--name-only"]
    if staged:
        args.append("--cached")
    else:
        args.append(base)
    try:
        out = _run_git(args)
        return [line for line in out.strip().splitlines() if line]
    except subprocess.CalledProcessError:
        return []


def get_recent_messages(limit: int = 5) -> list[str]:
    try:
        out = _run_git(["log", f"-{limit}", "--pretty=format:%s"])
        return [line for line in out.strip().splitlines() if line]
    except subprocess.CalledProcessError:
        return []


def get_diff_summary(base: str, staged: bool) -> str:
    args = ["diff", "--stat"]
    if staged:
        args.append("--cached")
    else:
        args.append(base)
    try:
        return _run_git(args)
    except subprocess.CalledProcessError:
        return "(diff indisponível)"


def detect_signals(stats: dict, files: list[str],
                   messages: list[str]) -> list[str]:
    signals: list[str] = []

    if stats["files"] >= THRESHOLDS["files"]:
        signals.append(
            f"{stats['files']} arquivos modificados "
            f"(limiar: {THRESHOLDS['files']})"
        )

    if stats["lines"] >= THRESHOLDS["lines"]:
        signals.append(
            f"{stats['lines']} linhas modificadas "
            f"(limiar: {THRESHOLDS['lines']})"
        )

    dep_changes = sorted({Path(f).name for f in files
                          if Path(f).name in DEPENDENCY_FILES})
    if dep_changes:
        signals.append("dependências alteradas: " + ", ".join(dep_changes))

    new_top_dirs = sorted({Path(f).parts[0] for f in files
                           if len(Path(f).parts) > 1})
    if len(new_top_dirs) >= 3:
        signals.append(
            f"mudanças em {len(new_top_dirs)} diretórios distintos: "
            + ", ".join(new_top_dirs[:5])
        )

    matched_msgs: list[str] = []
    for msg in messages:
        for pat in DECISION_KEYWORDS:
            if re.search(pat, msg, re.IGNORECASE):
                matched_msgs.append(msg)
                break
    if matched_msgs:
        signals.append(
            f"{len(matched_msgs)} mensagem(ns) com sinais de decisão"
        )

    return signals


def next_adr_number() -> int:
    nums: list[int] = []
    for f in DECISIONS_DIR.glob("[0-9]*.md"):
        if f.parent != DECISIONS_DIR:
            continue
        m = re.match(r"^(\d{4})-", f.name)
        if m:
            nums.append(int(m.group(1)))
    if PROPOSALS_DIR.exists():
        for f in PROPOSALS_DIR.glob("[0-9]*.md"):
            m = re.match(r"^(\d{4})-", f.name)
            if m:
                nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def generate_draft(stats: dict, files: list[str], messages: list[str],
                   signals: list[str]) -> tuple[str, str]:
    num = next_adr_number()
    today = date.today().isoformat()
    filename = f"{num:04d}-draft.md"

    file_list = "\n".join(f"- `{f}`" for f in files[:25])
    if len(files) > 25:
        file_list += f"\n- _... ({len(files) - 25} arquivos a mais)_"

    msg_list = "\n".join(f"- {m}" for m in messages) if messages else "- (nenhuma)"
    signal_list = ("\n".join(f"- {s}" for s in signals)
                   if signals else "- (nenhum sinal estrutural)")

    content = f"""---
id: ADR-{num:04d}
date: {today}
status: proposed
supersedes: null
superseded_by: null
affects_features: []
related: []
tags: []
---

# ADR-{num:04d} · TODO: título descritivo da decisão

> **DRAFT — proposta gerada automaticamente.**
> Revise, complete as seções TODO, renomeie com slug definitivo
> e mova de `decisions/proposals/` para `decisions/`.

## Sinais que motivaram esta proposta

{signal_list}

### Mensagens de commit recentes

{msg_list}

### Arquivos modificados ({stats["files"]} total)

{file_list}

## Contexto

TODO: descreva a situação que está exigindo uma decisão. Qual problema
estamos enfrentando? Qual restrição estamos atacando? Por que agora?

## Decisão

TODO: declare a escolha feita em uma ou duas frases. Use voz ativa.

## Consequências

TODO: liste tanto consequências positivas quanto negativas. Cada item
deve ser concreto o suficiente para ser refutável.

## Alternativas rejeitadas

TODO: para cada alternativa séria considerada, descreva por que foi
rejeitada. Esta é a seção mais importante do ADR.
"""
    return filename, content


PROMPT_TEMPLATE = """Você é um agente que ajuda a redigir Architecture Decision Records (ADRs).

Abaixo está o contexto de uma mudança recente em um projeto. Sua tarefa
é decidir se a mudança merece um ADR e, em caso afirmativo, propor um
draft completo seguindo o esquema padrão.

## Sinais detectados
{signals}

## Mensagens de commit recentes
{messages}

## Arquivos modificados
{files}

## Diff (resumo estatístico)
```
{diff}
```

## Tarefa

Se os sinais NÃO justificarem um ADR (mudança trivial, refactor mecânico,
sem trade-off explícito), responda apenas com:
"NÃO RECOMENDADO: <razão concisa>"

Se justificarem, produza um ADR completo neste formato:

```markdown
---
id: ADR-NNNN
date: YYYY-MM-DD
status: proposed
affects_features: [F-NNNN, ...]
tags: [...]
---

# ADR-NNNN · Título conciso e descritivo

## Contexto
(2-4 parágrafos sobre o problema, a restrição, e por que decidir agora)

## Decisão
(1-2 parágrafos sobre a escolha feita, em voz ativa)

## Consequências
(positivas e negativas, concretas e refutáveis)

## Alternativas rejeitadas
(cada uma com justificativa específica de rejeição)
```

Importante:
- A seção "Alternativas rejeitadas" é a mais valiosa do ADR. Não pule.
- Se você não tem informação suficiente para preencher uma seção,
  marque como "TODO: <pergunta específica>" em vez de inventar.
"""


def emit_prompt(stats: dict, files: list[str], messages: list[str],
                signals: list[str], base: str, staged: bool) -> None:
    diff_summary = get_diff_summary(base, staged)
    print(PROMPT_TEMPLATE.format(
        signals="\n".join(f"- {s}" for s in signals) or "- (nenhum)",
        messages="\n".join(f"- {m}" for m in messages) or "- (nenhuma)",
        files="\n".join(f"- {f}" for f in files[:30]) or "- (nenhum)",
        diff=diff_summary.strip() or "(diff vazio)",
    ))


def has_enough_history(base: str) -> tuple[bool, str]:
    """Verifica se a base ref existe e é alcançável a partir de HEAD."""
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--verify", base],
            text=True, stderr=subprocess.DEVNULL, cwd=ROOT,
        )
        return True, ""
    except subprocess.CalledProcessError:
        # Determina motivo provável
        try:
            count = subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"],
                text=True, stderr=subprocess.DEVNULL, cwd=ROOT,
            ).strip()
            n = int(count) if count.isdigit() else 0
            if base == "HEAD~1" and n < 2:
                return False, (
                    f"Repositório tem apenas {n} commit(s); "
                    f"--base HEAD~1 requer pelo menos 2. "
                    f"Use --staged para examinar mudanças staged."
                )
        except (subprocess.CalledProcessError, ValueError):
            pass
        return False, f"Ref '{base}' não encontrada no repositório."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="HEAD~1",
                        help="commit de referência (padrão: HEAD~1)")
    parser.add_argument("--staged", action="store_true",
                        help="examina mudanças staged em vez de --base")
    parser.add_argument("--force", action="store_true",
                        help="gera proposta mesmo sem sinais detectados")
    parser.add_argument("--prompt", action="store_true",
                        help="emite prompt para LLM em vez de gerar draft")
    args = parser.parse_args()

    if not (ROOT / ".git").exists():
        print(f"Erro: project root {ROOT} não é um repositório Git",
              file=sys.stderr)
        return 1

    # Validação prévia de base ref (apenas quando não usa --staged)
    if not args.staged:
        ok, reason = has_enough_history(args.base)
        if not ok:
            print(f"Erro: {reason}", file=sys.stderr)
            return 1

    stats = get_diff_stats(args.base, args.staged)
    files = get_changed_files(args.base, args.staged)
    messages = get_recent_messages()
    signals = detect_signals(stats, files, messages)

    if args.prompt:
        emit_prompt(stats, files, messages, signals, args.base, args.staged)
        return 0

    if not signals and not args.force:
        print("Nenhum sinal de decisão arquitetural detectado.")
        print(f"  Arquivos modificados: {stats['files']}")
        print(f"  Linhas modificadas:   {stats['lines']}")
        print("Use --force para gerar proposta mesmo assim.")
        return 0

    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)

    print("Sinais detectados:")
    for s in signals:
        print(f"  - {s}")

    filename, content = generate_draft(stats, files, messages, signals)
    output_path = PROPOSALS_DIR / filename
    output_path.write_text(content, encoding="utf-8")

    rel = output_path.relative_to(ROOT)
    print()
    print(f"Proposta gerada: {rel}")
    print()
    print("Próximos passos:")
    print(f"  1. Editar {rel} preenchendo as seções TODO")
    print("  2. Renomear o arquivo com slug descritivo")
    print(f"  3. mv {rel} decisions/<NNNN>-<slug>.md")
    print("  4. git add decisions/<NNNN>-<slug>.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
