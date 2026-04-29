#!/usr/bin/env python3
"""
deploy.py — Deploy idempotente da metodologia em um projeto.

Comportamento por arquivo:
    AGENT.md, CLAUDE.md  → merge inteligente se existem (skill memory-deploy)
    STATE.md             → pula se existe (conteúdo é volátil)
    skills/              → pula se existem (preserva customizações)
    pastas               → cria se não existem

Uso:
    python deploy.py             # padrão: merge AGENT/CLAUDE
    python deploy.py --force     # sobrescreve TUDO sem merge
    python deploy.py --no-merge  # pula se existe (sem merge)
    python deploy.py --no-hooks  # pula instalação de git hooks

Saída:
    Lista o que foi deployado, mesclado, criado e pulado.
    Quando merge é necessário, registra arquivos pendentes para a skill.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
SKILLS_DIR = SCRIPT_DIR / "skills"
TOOLS_DIR = SCRIPT_DIR / "tools"


def find_project_root(start: Path) -> Path:
    """Descobre o project root via git, com fallback para o pai do .agent-memory."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL, cwd=start,
        ).strip()
        if out:
            return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return start.parent


def find_python() -> str:
    """Localiza o interpretador Python disponível."""
    for candidate in ("python3", "python"):
        if shutil.which(candidate):
            return candidate
    print("ERRO: Python não encontrado no PATH", file=sys.stderr)
    sys.exit(1)


def deploy_constitution(root: Path, force: bool, merge: bool,
                        merge_queue: list[str]) -> None:
    """Deploy de AGENT.md e CLAUDE.md com lógica de merge."""
    print("Constituição (AGENT.md, CLAUDE.md):")
    pending_dir = SCRIPT_DIR / ".pending-merge"

    for template in ("AGENT.md", "CLAUDE.md"):
        src = TEMPLATES_DIR / template
        dst = root / template

        if not src.exists():
            print(f"  ERRO: template ausente: {src}", file=sys.stderr)
            sys.exit(1)

        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"  criado: {template}")
            continue

        if force:
            shutil.copy2(src, dst)
            print(f"  sobrescrito: {template} (--force)")
            continue

        if not merge:
            print(f"  pulado: {template} (já existe; --no-merge)")
            continue

        # Modo merge: registra para a skill processar
        pending_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, pending_dir / f"{template}.new")
        merge_queue.append(template)
        print(f"  pendente de merge: {template} (existente preservado)")


def deploy_state(root: Path, force: bool) -> None:
    """Deploy de STATE.md (sempre pula se existe; conteúdo é volátil)."""
    print("Estado (STATE.md):")
    src = TEMPLATES_DIR / "STATE.md"
    dst = root / "STATE.md"

    if not dst.exists():
        shutil.copy2(src, dst)
        print("  criado: STATE.md")
    elif force:
        shutil.copy2(src, dst)
        print("  sobrescrito: STATE.md (--force)")
    else:
        print("  pulado: STATE.md (já existe; foco da sessão é volátil)")


def deploy_gitattributes(root: Path) -> None:
    """Deploy do .gitattributes e configuração do driver de merge."""
    print("Configuração de merge (.gitattributes):")
    src = TEMPLATES_DIR / ".gitattributes"
    dst = root / ".gitattributes"

    if not src.exists():
        return

    if not dst.exists():
        shutil.copy2(src, dst)
        print("  criado: .gitattributes")
    else:
        # Anexa linhas que ainda não estão presentes
        existing = dst.read_text(encoding="utf-8")
        new_lines = src.read_text(encoding="utf-8").splitlines()
        appended_lines = []

        for line in new_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if line not in existing:
                appended_lines.append(line)

        if appended_lines:
            with dst.open("a", encoding="utf-8") as f:
                f.write("\n# Adicionado por .agent-memory/deploy.py\n")
                for line in appended_lines:
                    f.write(line + "\n")
            print("  anexado a: .gitattributes (regras de merge)")
        else:
            print("  já contém: .gitattributes (regras presentes)")

    # Configura driver `ours` no git local (idempotente)
    if (root / ".git").exists():
        try:
            subprocess.check_call(
                ["git", "config", "merge.ours.driver", "true"],
                cwd=root, stdout=subprocess.DEVNULL,
            )
            print("  configurado: merge.ours.driver")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  AVISO: não foi possível configurar merge.ours.driver")


def deploy_skills(root: Path, force: bool) -> None:
    """Deploy de skills para /skills/ no project root."""
    print("Skills:")
    skills_dst = root / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)

    if not SKILLS_DIR.exists():
        print("  AVISO: pasta skills/ ausente no pacote")
        return

    for skill_path in sorted(SKILLS_DIR.iterdir()):
        if not skill_path.is_dir():
            continue
        skill_name = skill_path.name
        src_file = skill_path / "SKILL.md"
        dst_dir = skills_dst / skill_name
        dst_file = dst_dir / "SKILL.md"

        if not src_file.exists():
            print(f"  pulado: {skill_name} (sem SKILL.md no source)")
            continue

        if dst_file.exists() and not force:
            print(f"  pulado: {skill_name} (já existe; use --force)")
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            print(f"  deployada: {skill_name}")


def create_directories(root: Path) -> None:
    """Cria estrutura de pastas no project root."""
    print("Estrutura de pastas:")
    for rel in ("manifest/features", "decisions/proposals"):
        full = root / rel
        if full.exists():
            print(f"  já existe: {rel}/")
        else:
            full.mkdir(parents=True, exist_ok=True)
            (full / ".gitkeep").touch()
            print(f"  criado: {rel}/")


def install_hooks(root: Path) -> None:
    """Instala git hooks (delega para install_hooks.py)."""
    print("Git hooks:")
    if not (root / ".git").exists():
        print("  pulado (não é repositório Git)")
        return

    hooks_module = TOOLS_DIR / "install_hooks.py"
    if not hooks_module.exists():
        print("  AVISO: install_hooks.py não encontrado")
        return

    py = find_python()
    try:
        result = subprocess.run(
            [py, str(hooks_module)],
            check=False, capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            print(f"  {line}")
        if result.returncode != 0:
            print(f"  AVISO: install_hooks.py retornou {result.returncode}")
    except Exception as e:
        print(f"  AVISO: falha ao instalar hooks: {e}")


def write_installed_version(root: Path) -> None:
    """Registra a versão instalada no project root."""
    version_file = SCRIPT_DIR / "VERSION"
    if not version_file.exists():
        return

    version = version_file.read_text(encoding="utf-8").strip()
    installed_marker = SCRIPT_DIR / ".installed-version"
    installed_marker.write_text(version + "\n", encoding="utf-8")


def run_audit(root: Path, has_pending_merge: bool) -> None:
    """Roda primeira auditoria (apenas se não há merges pendentes)."""
    if has_pending_merge:
        print("Auditoria inicial: ADIADA até resolução de merges pendentes.")
        return

    print("Auditoria inicial:")
    py = find_python()
    audit_script = TOOLS_DIR / "audit.py"

    try:
        result = subprocess.run(
            [py, str(audit_script)],
            check=False, capture_output=True, text=True, cwd=root,
        )
        for line in result.stdout.splitlines():
            print(f"  {line}")
        if result.returncode != 0:
            print(f"  AVISO: auditoria retornou {result.returncode}")
    except Exception as e:
        print(f"  AVISO: falha ao rodar auditoria: {e}")


def print_next_steps(root: Path, merge_queue: list[str]) -> None:
    """Imprime próximos passos para o usuário."""
    if merge_queue:
        print("ATENÇÃO: arquivos pendentes de merge:")
        for f in merge_queue:
            print(f"  - {f} (template novo em .agent-memory/.pending-merge/{f}.new)")
        print()
        print("Próximo passo: peça ao agente para mesclar:")
        print('  "resolva os merges pendentes do deploy"')
        print()
        print("A skill memory-deploy fará o merge preservando seu conteúdo")
        print("e adicionando o que está faltando do template novo.")
    else:
        print("Próximos passos:")
        print(f"  1. Personalize {root}/AGENT.md (project, stack, constraints)")
        print(f"  2. Personalize {root}/STATE.md (Current, Next)")
        print("  3. Crie sua primeira feature em manifest/features/")
        print("  4. Faça commit: git add . && git commit -m 'adopt agent memory'")
    print()
    print("Documentação: .agent-memory/USER_GUIDE.md")
    print("Skills (deployadas): skills/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="sobrescreve TUDO sem merge")
    parser.add_argument("--no-merge", action="store_true",
                        help="pula arquivos existentes em vez de mesclar")
    parser.add_argument("--no-hooks", action="store_true",
                        help="pula instalação de git hooks")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = find_project_root(SCRIPT_DIR)

    print("=" * 38)
    print("Deploy da metodologia de memória")
    print("=" * 38)

    version_file = SCRIPT_DIR / "VERSION"
    if version_file.exists():
        version = version_file.read_text(encoding="utf-8").strip()
        print(f"Versão: {version}")
    print(f"Project root: {root}")
    print()

    # Limpa fila de merge anterior
    merge_queue_file = SCRIPT_DIR / ".merge-queue"
    if merge_queue_file.exists():
        merge_queue_file.unlink()

    merge_queue: list[str] = []

    deploy_constitution(root, args.force, not args.no_merge, merge_queue)
    print()

    deploy_state(root, args.force)
    print()

    deploy_gitattributes(root)
    print()

    deploy_skills(root, args.force)
    print()

    create_directories(root)
    print()

    if not args.no_hooks:
        install_hooks(root)
    else:
        print("Git hooks: pulado (--no-hooks)")
    print()

    if merge_queue:
        merge_queue_file.write_text(
            "\n".join(merge_queue) + "\n", encoding="utf-8"
        )

    run_audit(root, has_pending_merge=bool(merge_queue))
    print()

    write_installed_version(root)

    print("=" * 38)
    print("Deploy concluído.")
    print("=" * 38)
    print()

    print_next_steps(root, merge_queue)

    return 0


if __name__ == "__main__":
    sys.exit(main())
