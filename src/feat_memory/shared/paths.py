"""paths.py — Globais de path do projeto, lazy-init.

ROOT/AGENT/STATE/etc são populados preguiçosamente via `_init_paths()`
na primeira chamada. Importar o módulo (ex.: para registrar subparsers
via cli.py) não dispara `git rev-parse`.

ADR-0021: parte de `shared/`, sem dependências do projeto. Antes desta
separação, esses globais viviam em `audit.py` e eram acessados por outros
módulos via `audit.ROOT`, criando acoplamento de governance → memory.
Centralizar aqui quebra esse acoplamento.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def find_project_root() -> Path:
    """Descobre o project root via git, com fallback para o cwd."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    current = Path.cwd().resolve()
    for _ in range(5):
        if (current / "AGENTS.md").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return Path.cwd()


# Paths globais lazy. None até primeira chamada de _init_paths().
ROOT: Path = None  # type: ignore[assignment]
AGENT: Path = None  # type: ignore[assignment]
CLAUDE: Path = None  # type: ignore[assignment]
STATE: Path = None  # type: ignore[assignment]
MANIFEST_DIR: Path = None  # type: ignore[assignment]
FEATURES_DIR: Path = None  # type: ignore[assignment]
ARCHIVE_DIR: Path = None  # type: ignore[assignment]
DECISIONS_DIR: Path = None  # type: ignore[assignment]
SUPERSEDED_DIR: Path = None  # type: ignore[assignment]
PROPOSALS_DIR: Path = None  # type: ignore[assignment]


def _init_paths(root: Path | None = None) -> None:
    """Resolve ROOT e dependentes. Idempotente.

    Sem argumento, descobre o root via `find_project_root()` (git/cwd). Com
    `root` explícito (subcomandos que aceitam `[path]` opcional, ADR-0033),
    usa-o — desde que seja a primeira chamada ou que aponte para o mesmo root
    já resolvido. Um override divergente após o root já estar fixado é
    reaplicado (recomputa os derivados), porque cada `run` resolve seu próprio
    alvo uma vez.
    """
    global ROOT, AGENT, CLAUDE, STATE
    global MANIFEST_DIR, FEATURES_DIR, ARCHIVE_DIR
    global DECISIONS_DIR, SUPERSEDED_DIR, PROPOSALS_DIR
    if ROOT is not None and (root is None or root == ROOT):
        return
    ROOT = root if root is not None else find_project_root()
    AGENT = ROOT / "AGENTS.md"
    CLAUDE = ROOT / "CLAUDE.md"
    STATE = ROOT / ".feat-memory" / "STATE.md"
    MANIFEST_DIR = ROOT / ".feat-memory" / "manifest"
    FEATURES_DIR = MANIFEST_DIR / "features"
    ARCHIVE_DIR = MANIFEST_DIR / "archive"
    DECISIONS_DIR = ROOT / ".feat-memory" / "decisions"
    SUPERSEDED_DIR = DECISIONS_DIR / "superseded"
    PROPOSALS_DIR = DECISIONS_DIR / "proposals"
