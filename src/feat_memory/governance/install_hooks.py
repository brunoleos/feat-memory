"""install_hooks.py — Instala os Git hooks no projeto consumidor.

Chamado pelo deploy via install_hooks.install(target). Idempotente.
Os hooks ficam em src/feat_memory/data/hooks/ e são acessados via
importlib.resources (funciona em editable e wheel install).
"""

from __future__ import annotations

import shutil
import stat
from importlib.resources import as_file, files
from pathlib import Path


def install(target: Path) -> int:
    """Copia hooks do pacote para <target>/.git/hooks/.

    Retorna 0 se ok ou se target não é repositório Git (apenas avisa).
    """
    git_dir = target / ".git"
    if not git_dir.exists():
        print("  pulado (não é repositório Git)")
        return 0

    hooks_dst = git_dir / "hooks"
    hooks_dst.mkdir(parents=True, exist_ok=True)

    hooks_src = files("feat_memory.governance") / "data" / "hooks"

    installed = 0
    for entry in sorted(hooks_src.iterdir(), key=lambda e: e.name):
        if not entry.is_file():
            continue
        hook_name = entry.name
        with as_file(entry) as src_path:
            dst = hooks_dst / hook_name
            shutil.copy2(src_path, dst)
            current = dst.stat().st_mode
            dst.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"  instalado: {hook_name}")
        installed += 1

    print(f"  {installed} hook(s) em {hooks_dst}")
    print("  Para desabilitar temporariamente um commit: git commit --no-verify")
    return 0
