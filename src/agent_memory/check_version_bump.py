"""check_version_bump.py — Bloqueia commits que tocam código sem bumpar VERSION.

Subcomando da CLI: `agent-memory check-version-bump-staged`. Inspeciona o
índice via `git diff --cached --name-only` e exige que `VERSION` esteja
no staging quando há paths de código também staged.

Zero-config e auto opt-in: se não existe arquivo `VERSION` na raiz do
projeto, é no-op (exit 0). Projetos que adotam o arquivo `VERSION` como
fonte da verdade ganham o guard automaticamente após `agent-memory deploy`.

Reusa `_is_code_path` de audit.py para coerência com a heurística do
check-staleness (mesma definição de "código" para os dois guards).

Para contornar deliberadamente: git commit --no-verify
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from agent_memory import audit


VERSION_FILE = "VERSION"

ERROR_TEXT = (
    "agent-memory: commit toca código mas VERSION não foi atualizado.\n"
    "  Bump conforme SemVer:\n"
    "    - patch (0.0.X) para correção pequena\n"
    "    - minor (0.X.0) para nova feature\n"
    "    - major (X.0.0) para breaking change na API\n"
    "  Para contornar: git commit --no-verify"
)


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


def needs_bump(root: Path) -> bool:
    """Decide se o commit corrente deve ser bloqueado.

    True = bloquear (há código staged sem bump de VERSION).
    Núcleo testável; `run()` cuida do exit code e da impressão.
    """
    if not (root / VERSION_FILE).is_file():
        return False

    paths = _staged_paths(root)
    if not paths:
        return False

    has_code = any(audit._is_code_path(p) for p in paths)
    if not has_code:
        return False

    version_staged = any(
        p.replace("\\", "/") == VERSION_FILE for p in paths
    )
    return not version_staged


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "check-version-bump-staged",
        help="Bloqueia commits que tocam código sem bumpar VERSION "
             "(usado pelo pre-commit hook; no-op se VERSION não existe)",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    audit._init_paths()
    if not needs_bump(audit.ROOT):
        return 0

    if sys.stderr.isatty():
        print(f"\033[31m{ERROR_TEXT}\033[0m", file=sys.stderr)
    else:
        print(ERROR_TEXT, file=sys.stderr)
    return 1
