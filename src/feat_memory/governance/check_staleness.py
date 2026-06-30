"""check_staleness.py — Aviso soft no momento do commit.

Subcomando da CLI: `feat-memory check-staleness-staged`. Inspeciona o
índice via `git diff --cached --name-only` e emite warning na stderr
se há paths de código sem registro simultâneo no changelog/UNRELEASED.md.
Sempre exit 0 (fail-open por ADR-0008, soft por ADR-0016).

Reusa a heurística `_is_code_path` de audit.py para coerência com o
check de --check-staleness (F-0011, ADR-0014). Diferença é o ponto
temporal: F-0011 olha `git log` retroativo; F-0013 olha o índice atual.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from feat_memory.shared import paths as _paths
from feat_memory.governance import audit


WARNING_TEXT = (
    "feat-memory: commit toca código sem registrar no changelog/UNRELEASED.md "
    "— considere /memory-debrief"
)
WARNING_PREFIX = "⚠ "


def _staged_paths(root: Path) -> list[str] | None:
    """Lê `git diff --cached --name-only` no root. None se git falhar."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            text=True, stderr=subprocess.DEVNULL, cwd=root,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [line.strip() for line in out.splitlines() if line.strip()]


def staged_warning(root: Path) -> str | None:
    """Retorna o texto do warning ou None.

    Núcleo testável da feature — não imprime, apenas decide. A camada
    `run()` cuida de cor, isatty e stderr.
    """
    paths = _staged_paths(root)
    if not paths:
        return None

    unreleased_relpath = ".feat-memory/changelog/UNRELEASED.md"
    if any(p.replace("\\", "/") == unreleased_relpath for p in paths):
        return None

    has_code = any(audit._is_code_path(p) for p in paths)
    if not has_code:
        return None

    return WARNING_TEXT


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "check-staleness-staged",
        help="Avisa se o staging toca código sem registrar no "
             "changelog/UNRELEASED.md (soft, sempre exit 0; pre-commit hook)",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    _paths._init_paths()
    text = staged_warning(_paths.ROOT)
    if text is None:
        return 0

    if sys.stderr.isatty():
        # ANSI yellow + reset; só em terminal interativo
        print(f"\033[33m{WARNING_PREFIX}{text}\033[0m", file=sys.stderr)
    else:
        print(f"{WARNING_PREFIX}{text}", file=sys.stderr)

    return 0
