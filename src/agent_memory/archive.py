"""archive.py — Move features shipped fora de active_features para archive/.

Subcomando da CLI: `agent-memory archive [--apply]`. Default é dry-run
(lista o que seria arquivado, sai sem mover). Política em ADR-0015.

Critério de elegibilidade:
    status == "shipped" E id ∉ STATE.md::active_features

Movimento:
    `git mv` quando em repo Git (preserva blame); fallback `shutil.move`.
    Após mover, regenera manifest/INDEX.md e manifest/archive/INDEX.md.

ADRs nunca são arquivados — não há opção, é registro histórico imutável.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from agent_memory import audit


def collect_eligible(features_dir: Path,
                     state_fm: dict) -> list[tuple[Path, dict]]:
    """Lista features que satisfazem (shipped E não-ativa).

    Retorna pares (path, frontmatter) ordenados por id. Erros de
    parsing de frontmatter são silenciosamente puladas — `audit`
    é o lugar para validar schema, não este subcomando.
    """
    active_ids = set(state_fm.get("active_features") or [])
    eligible: list[tuple[Path, dict]] = []

    if not features_dir.exists():
        return eligible

    for fp in sorted(features_dir.glob("F-*.md")):
        try:
            fm, _ = audit.parse_frontmatter(fp)
        except ValueError:
            continue
        if fm.get("status") != "shipped":
            continue
        if fm.get("id") in active_ids:
            continue
        eligible.append((fp, fm))

    return eligible


def _move(src: Path, dst: Path, root: Path) -> str:
    """Move src para dst. Tenta `git mv`, fallback `shutil.move`.

    Retorna o método usado: "git" ou "fs".
    """
    src_rel = src.relative_to(root)
    dst_rel = dst.relative_to(root)
    try:
        subprocess.check_call(
            ["git", "mv", str(src_rel), str(dst_rel)],
            cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return "git"
    except (subprocess.CalledProcessError, FileNotFoundError):
        shutil.move(str(src), str(dst))
        return "fs"


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "archive",
        help="Move features shipped (e fora de active_features) para "
             "manifest/archive/",
    )
    p.add_argument("--apply", action="store_true",
                   help="executa o movimento; sem esta flag, é dry-run")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    audit._init_paths()

    state_fm: dict = {}
    if audit.STATE.exists():
        try:
            state_fm, _ = audit.parse_frontmatter(audit.STATE)
        except ValueError as e:
            print(f"ERRO ao ler STATE.md: {e}", file=sys.stderr)
            return 1

    eligible = collect_eligible(audit.FEATURES_DIR, state_fm)

    if not eligible:
        print("Nenhuma feature elegível ao arquivamento.")
        print("(critério: status == 'shipped' E id ∉ STATE.md::active_features)")
        return 0

    print(f"{len(eligible)} feature(s) elegível(eis) ao arquivamento:")
    for fp, fm in eligible:
        print(f"  - {fm.get('id', '?')}  {fp.name}")

    if not args.apply:
        print()
        print("[dry-run] Nada foi movido. Use --apply para confirmar.")
        return 0

    archive_dir = audit.MANIFEST_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("Movendo:")
    moved: list[tuple[Path, dict]] = []
    for fp, fm in eligible:
        dst = archive_dir / fp.name
        method = _move(fp, dst, audit.ROOT)
        marker = "git mv" if method == "git" else "fs (sem git)"
        print(f"  {marker}: {fp.name}")
        moved.append((dst, fm))

    print()
    print("Regenerando índices:")
    result = audit.run_audit(write_indices=True)
    issues_count = len(result["issues"])
    if issues_count:
        print(f"  audit reportou {issues_count} issue(s); rode "
              "`agent-memory audit` para detalhes")
    else:
        print("  audit limpo.")

    return 0
