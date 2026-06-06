"""check_doc_sync.py — Gate hard de sincronização doc↔código no commit.

Subcomando da CLI: `feat-memory check-doc-sync-staged`. Inspeciona o índice
via `git diff --cached --name-only` e **bloqueia** (exit 1) quando há paths de
código staged sem que NENHUM artefato de documentação esteja no mesmo staging —
ou seja, código mudando sem o Manifest/decisões/STATE acompanhar.

Relação com `check_staleness` (F-0013, ADR-0016): o staleness-check é **soft**
(sempre exit 0) e só olha `STATE.md` — um nudge. Este é **hard** (exit 1) e
aceita qualquer um de `STATE.md`, `manifest/**` ou `decisions/**` como prova de
que a doc se moveu. O soft nudga para o STATE; o hard garante que algo de doc
acompanhou o código. Fail-soft sem git (a fail-open de binário-ausente é no hook).

Reusa `_is_code_path` de audit.py (mesma heurística do staleness) e `_staged_paths`
de check_staleness.py (mesma leitura do índice).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from feat_memory.shared import paths as _paths
from feat_memory.governance import audit
from feat_memory.governance.check_staleness import _staged_paths


MEMORY_DIR = ".feat-memory"

BLOCK_TEXT = (
    "feat-memory: o commit toca código sem mover nenhum artefato de doc em "
    f"{MEMORY_DIR}/ (STATE.md, manifest/ ou decisions/). "
    "Rode /memory-debrief antes de commitar, ou contorne com "
    "`git commit --no-verify`."
)
BLOCK_PREFIX = "✗ "


def _is_doc_path(path: str) -> bool:
    """True se o path é um artefato de doc cujo update satisfaz o gate."""
    p = path.replace("\\", "/")
    return (
        p == f"{MEMORY_DIR}/STATE.md"
        or p.startswith(f"{MEMORY_DIR}/manifest/")
        or p.startswith(f"{MEMORY_DIR}/decisions/")
    )


def staged_block_reason(root: Path) -> str | None:
    """Retorna o texto do bloqueio ou None.

    Núcleo testável — não imprime nem sai, apenas decide. None quando: nada
    staged, nenhum código staged, ou algum artefato de doc staged.
    """
    paths = _staged_paths(root)
    if not paths:
        return None
    norm = [p.replace("\\", "/") for p in paths]
    if not any(audit._is_code_path(p) for p in norm):
        return None
    if any(_is_doc_path(p) for p in norm):
        return None
    return BLOCK_TEXT


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "check-doc-sync-staged",
        help="Bloqueia (exit 1) se o staging toca código sem mover doc em "
             f"{MEMORY_DIR}/ (STATE/manifest/decisions); usado pelo pre-commit hook",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    _paths._init_paths()
    reason = staged_block_reason(_paths.ROOT)
    if reason is None:
        return 0

    if sys.stderr.isatty():
        print(f"\033[31m{BLOCK_PREFIX}{reason}\033[0m", file=sys.stderr)
    else:
        print(f"{BLOCK_PREFIX}{reason}", file=sys.stderr)

    return 1
