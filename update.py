#!/usr/bin/env python3
"""
update.py — Atualiza a metodologia para a versão mais recente do upstream.

Estratégia:
    1. Lê a versão instalada de .installed-version
    2. Busca a versão mais recente do upstream (via git ou HTTP)
    3. Se há atualização, baixa e substitui o conteúdo de .agent-memory/
       (preservando .installed-version, .merge-queue, .pending-merge/)
    4. Re-roda o deploy.py para propagar mudanças aos artefatos do projeto
       (com a lógica de merge para AGENT.md/CLAUDE.md)

Configuração:
    O upstream é configurado em .agent-memory/.upstream com uma das opções:
        git+<URL>           # ex: git+https://github.com/user/agent-memory.git
        git+<URL>#<ref>     # ex: git+https://github.com/user/agent-memory.git#v0.2.0
        local:<path>        # ex: local:/home/user/agent-memory

Uso:
    python update.py              # atualiza para a versão upstream
    python update.py --check      # apenas verifica sem aplicar
    python update.py --dry-run    # mostra o que seria feito
    python update.py --to <ver>   # atualiza para versão específica
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INSTALLED_VERSION_FILE = SCRIPT_DIR / ".installed-version"
UPSTREAM_CONFIG_FILE = SCRIPT_DIR / ".upstream"
VERSION_FILE = SCRIPT_DIR / "VERSION"

PRESERVE_FILES = {
    ".installed-version",
    ".upstream",
    ".merge-queue",
}
PRESERVE_DIRS = {
    ".pending-merge",
}


def parse_version(s: str) -> tuple[int, int, int]:
    """Parse versão semântica em tupla comparável."""
    parts = s.strip().lstrip("v").split(".")
    if len(parts) != 3:
        raise ValueError(f"versão inválida: {s}")
    return tuple(int(p) for p in parts)  # type: ignore


def get_installed_version() -> str | None:
    """Lê a versão instalada, ou None se ausente."""
    if INSTALLED_VERSION_FILE.exists():
        return INSTALLED_VERSION_FILE.read_text(encoding="utf-8").strip()
    if VERSION_FILE.exists():
        # Compatibilidade: sem .installed-version, assume VERSION atual
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return None


def get_upstream_config() -> str | None:
    """Lê configuração do upstream."""
    if not UPSTREAM_CONFIG_FILE.exists():
        return None
    return UPSTREAM_CONFIG_FILE.read_text(encoding="utf-8").strip()


def fetch_upstream(upstream: str, target_ref: str | None) -> Path:
    """Baixa o upstream para uma pasta temporária e retorna o path."""
    tmp = Path(tempfile.mkdtemp(prefix="agent-memory-update-"))

    if upstream.startswith("git+"):
        url = upstream[4:]
        ref = None
        if "#" in url:
            url, ref = url.rsplit("#", 1)
        if target_ref:
            ref = target_ref

        clone_cmd = ["git", "clone", "--quiet", url, str(tmp)]
        subprocess.check_call(clone_cmd, stderr=subprocess.DEVNULL)

        if ref:
            subprocess.check_call(
                ["git", "checkout", "--quiet", ref],
                cwd=tmp, stderr=subprocess.DEVNULL,
            )

        candidate = tmp / ".agent-memory"
        if candidate.exists():
            return candidate
        return tmp

    if upstream.startswith("local:"):
        path = Path(upstream[6:]).expanduser().resolve()
        if not path.exists():
            shutil.rmtree(tmp, ignore_errors=True)
            raise FileNotFoundError(f"local upstream não existe: {path}")

        candidate = path / ".agent-memory"
        if candidate.exists():
            return candidate
        return path

    shutil.rmtree(tmp, ignore_errors=True)
    raise ValueError(f"upstream não reconhecido: {upstream}")


def get_upstream_version(upstream_dir: Path) -> str:
    """Lê a versão do upstream baixado."""
    version_file = upstream_dir / "VERSION"
    if not version_file.exists():
        raise FileNotFoundError(
            f"upstream não tem arquivo VERSION em {version_file}"
        )
    return version_file.read_text(encoding="utf-8").strip()


def replace_package_contents(upstream_dir: Path, dry_run: bool = False) -> None:
    """Substitui o conteúdo de .agent-memory/ preservando arquivos específicos."""
    # Salva arquivos preservados
    preserved: dict[str, bytes] = {}
    preserved_dirs: dict[str, Path] = {}

    for name in PRESERVE_FILES:
        path = SCRIPT_DIR / name
        if path.exists():
            preserved[name] = path.read_bytes()

    for name in PRESERVE_DIRS:
        path = SCRIPT_DIR / name
        if path.exists() and path.is_dir():
            tmp_save = Path(tempfile.mkdtemp(prefix=f"preserve-{name}-"))
            shutil.copytree(path, tmp_save / name)
            preserved_dirs[name] = tmp_save / name

    if dry_run:
        print("DRY-RUN: substituiria conteúdo de .agent-memory/ pelo upstream")
        for name, tmp_save in preserved_dirs.items():
            shutil.rmtree(tmp_save.parent, ignore_errors=True)
        return

    # Remove conteúdo atual (exceto arquivos/pastas preservadas)
    for item in SCRIPT_DIR.iterdir():
        if item.name in PRESERVE_FILES or item.name in PRESERVE_DIRS:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # Copia novo conteúdo do upstream
    for item in upstream_dir.iterdir():
        if item.name in PRESERVE_FILES or item.name in PRESERVE_DIRS:
            continue
        dst = SCRIPT_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)

    # Restaura preservados (apenas se não vierem do upstream)
    for name, content in preserved.items():
        path = SCRIPT_DIR / name
        if not path.exists():
            path.write_bytes(content)

    for name, tmp_save in preserved_dirs.items():
        path = SCRIPT_DIR / name
        if not path.exists():
            shutil.copytree(tmp_save, path)
        shutil.rmtree(tmp_save.parent, ignore_errors=True)


def run_redeploy() -> int:
    """Re-roda o deploy.py para propagar mudanças."""
    py = shutil.which("python3") or shutil.which("python")
    if py is None:
        print("ERRO: Python não encontrado no PATH", file=sys.stderr)
        return 1

    deploy_script = SCRIPT_DIR / "deploy.py"
    if not deploy_script.exists():
        print("ERRO: deploy.py não encontrado", file=sys.stderr)
        return 1

    print()
    print("=" * 38)
    print("Re-deploy para propagar atualização")
    print("=" * 38)
    result = subprocess.run([py, str(deploy_script)])
    return result.returncode


def write_installed_version(version: str) -> None:
    """Atualiza .installed-version."""
    INSTALLED_VERSION_FILE.write_text(version + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="apenas verifica se há atualização")
    parser.add_argument("--dry-run", action="store_true",
                        help="mostra o que seria feito sem aplicar")
    parser.add_argument("--to", metavar="VERSION",
                        help="atualiza para versão específica (ex: v0.2.0)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 38)
    print("Update da metodologia de memória")
    print("=" * 38)

    upstream = get_upstream_config()
    if upstream is None:
        print()
        print("ERRO: upstream não configurado.")
        print()
        print("Crie .agent-memory/.upstream com uma linha indicando a fonte:")
        print("  git+https://github.com/usuario/agent-memory.git")
        print("  git+https://github.com/usuario/agent-memory.git#v0.2.0")
        print("  local:/home/usuario/agent-memory")
        return 1

    installed = get_installed_version()
    print(f"Versão instalada: {installed or '(desconhecida)'}")
    print(f"Upstream:         {upstream}")
    print()

    print("Buscando upstream...")
    try:
        upstream_dir = fetch_upstream(upstream, args.to)
    except Exception as e:
        print(f"ERRO ao buscar upstream: {e}", file=sys.stderr)
        return 1

    try:
        upstream_version = get_upstream_version(upstream_dir)
        print(f"Versão upstream:  {upstream_version}")
        print()

        if installed:
            try:
                inst_t = parse_version(installed)
                up_t = parse_version(upstream_version)
                if inst_t == up_t:
                    print("Já está na versão mais recente. Nada a fazer.")
                    return 0
                if inst_t > up_t:
                    print("AVISO: versão instalada é mais recente que o upstream.")
                    if not args.to:
                        print("Use --to <versão> para forçar downgrade.")
                        return 1
            except ValueError:
                pass

        if args.check:
            print(f"Atualização disponível: {installed} → {upstream_version}")
            return 0

        if args.dry_run:
            print(f"DRY-RUN: atualizaria de {installed} para {upstream_version}")
            replace_package_contents(upstream_dir, dry_run=True)
            return 0

        print(f"Atualizando: {installed} → {upstream_version}")
        replace_package_contents(upstream_dir, dry_run=False)
        write_installed_version(upstream_version)
        print(f"Pacote atualizado para {upstream_version}.")

        rc = run_redeploy()
        if rc != 0:
            print(f"AVISO: re-deploy retornou {rc}. "
                  "Verifique a saída acima.")
            return rc

        print()
        print("Atualização concluída.")
        return 0

    finally:
        if upstream.startswith("git+"):
            # Limpa diretório temporário do clone
            parent = upstream_dir
            while parent.parent != parent:
                if parent.parent.name.startswith("agent-memory-update-"):
                    parent = parent.parent
                    break
                parent = parent.parent
            if parent.name.startswith("agent-memory-update-"):
                shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
