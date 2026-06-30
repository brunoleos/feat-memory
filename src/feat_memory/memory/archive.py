"""archive.py — Move features shipped fora de active_features para archive/.

Subcomando da CLI: `feat-memory archive [--apply]`. Default é dry-run
(lista o que seria arquivado, sai sem mover). Política em ADR-0015.

Critério de elegibilidade:
    status == "shipped" E id ∉ refs ativas (derivadas do changelog/UNRELEASED.md;
    com fallback para STATE.md::active_features se um consumidor legado o tiver)

Movimento:
    `git mv` quando em repo Git (preserva blame); fallback `shutil.move`.
    Após mover, regenera manifest/INDEX.md e manifest/archive/INDEX.md
    via `memory.indexing.regenerate_all_indexes` — não chama governance.

ADRs nunca são arquivados — não há opção, é registro histórico imutável.
ADR-0021: vive em memory/ porque archive é ciclo de vida de artefatos,
não enforcement.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from feat_memory.shared import paths as _paths
from feat_memory.shared.parsing import parse_frontmatter
from feat_memory.memory import indexing, schemas


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
            fm, _ = parse_frontmatter(fp)
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


def _load_features_and_decisions(features_dir: Path,
                                  archive_dir: Path,
                                  decisions_dir: Path,
                                  superseded_dir: Path) -> tuple[list[dict],
                                                                  list[dict],
                                                                  list[dict],
                                                                  list[dict]]:
    """Carrega frontmatters de features (ativas/arquivadas) e decisions
    (principal/superseded).

    Sem validação — `audit` é quem valida. Aqui só precisamos dos dados
    para alimentar a regeneração de INDEXes pós-move.
    """
    def _load(d: Path, glob: str, *, only_direct: bool = False) -> list[dict]:
        out: list[dict] = []
        if not d.exists():
            return out
        for fp in sorted(d.glob(glob)):
            if only_direct and fp.parent != d:
                continue
            try:
                fm, _ = parse_frontmatter(fp)
                if fm:
                    out.append(fm)
            except ValueError:
                continue
        return out

    features = _load(features_dir, "F-*.md")
    archived = _load(archive_dir, "F-*.md")
    decisions = _load(decisions_dir, "[0-9]*.md", only_direct=True)
    superseded = _load(superseded_dir, "[0-9]*.md", only_direct=True)
    return features, archived, decisions, superseded


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
    _paths._init_paths()

    from feat_memory.memory import changelog
    active = set(changelog.derive_active_refs(_paths.ROOT)["features"])
    # Backward-compat: se um consumidor legado ainda tem STATE.md, soma o active dele.
    if _paths.STATE.exists():
        try:
            legacy_fm, _ = parse_frontmatter(_paths.STATE)
            active |= set(legacy_fm.get("active_features") or [])
        except ValueError as e:
            print(f"ERRO ao ler STATE.md legado: {e}", file=sys.stderr)
            return 1
    state_fm = {"active_features": sorted(active)}

    eligible = collect_eligible(_paths.FEATURES_DIR, state_fm)

    if not eligible:
        print("Nenhuma feature elegível ao arquivamento.")
        print("(critério: status == 'shipped' E não referenciada no "
              "changelog/UNRELEASED.md)")
        return 0

    print(f"{len(eligible)} feature(s) elegível(eis) ao arquivamento:")
    for fp, fm in eligible:
        print(f"  - {fm.get('id', '?')}  {fp.name}")

    if not args.apply:
        print()
        print("[dry-run] Nada foi movido. Use --apply para confirmar.")
        return 0

    archive_dir = _paths.MANIFEST_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("Movendo:")
    for fp, fm in eligible:
        dst = archive_dir / fp.name
        method = _move(fp, dst, _paths.ROOT)
        marker = "git mv" if method == "git" else "fs (sem git)"
        print(f"  {marker}: {fp.name}")

    print()
    print("Regenerando índices:")
    features, archived, decisions, superseded = _load_features_and_decisions(
        _paths.FEATURES_DIR, archive_dir,
        _paths.DECISIONS_DIR, _paths.SUPERSEDED_DIR,
    )
    indexing.regenerate_all_indexes(
        _paths.MANIFEST_DIR, archive_dir,
        _paths.DECISIONS_DIR, _paths.SUPERSEDED_DIR,
        features, archived, decisions, superseded,
    )
    print(f"  manifest/INDEX.md: {len(features)} features ativas")
    print(f"  manifest/archive/INDEX.md: {len(archived)} arquivadas")
    print(f"  decisions/INDEX.md: {len(decisions)} decisões")
    if superseded:
        print(f"  decisions/superseded/INDEX.md: {len(superseded)} superseded")

    return 0
