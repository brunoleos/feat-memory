#!/usr/bin/env python3
"""
install_hooks.py — Instala os Git hooks do projeto em .git/hooks/.

Idempotente: pode ser rodado quantas vezes quiser.

Uso:
    python install_hooks.py
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
HOOKS_SRC = SCRIPT_DIR / "hooks"


def find_project_root() -> Path:
    """Descobre a raiz do repositório Git."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    print("Erro: não é um repositório Git", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    root = find_project_root()
    hooks_dst = root / ".git" / "hooks"

    if not HOOKS_SRC.exists() or not HOOKS_SRC.is_dir():
        print(f"Erro: pasta de hooks não encontrada em {HOOKS_SRC}",
              file=sys.stderr)
        return 1

    hooks_dst.mkdir(parents=True, exist_ok=True)

    installed = 0
    for hook_path in sorted(HOOKS_SRC.iterdir()):
        if not hook_path.is_file():
            continue
        hook_name = hook_path.name
        dst = hooks_dst / hook_name

        shutil.copy2(hook_path, dst)
        # Garante permissão de execução (0o755)
        current = dst.stat().st_mode
        dst.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"instalado: {hook_name}")
        installed += 1

    print()
    print(f"{installed} hook(s) instalados em {hooks_dst}")
    print("Para desabilitar temporariamente um commit: git commit --no-verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
