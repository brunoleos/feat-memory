"""changelog.py — Histórico como pasta por-tag + UNRELEASED vivo.

Substitui (em fases) o CHANGELOG.md monolítico — deprecando Keep-a-Changelog
(ADR-0042) — e o STATE.md, dissolvido no UNRELEASED (ADR-0043). Cada release
tagueada vira um arquivo imutável `.feat-memory/changelog/<X.Y.Z>.md`; o
trabalho concluído-mas-não-lançado vive em `changelog/UNRELEASED.md`;
`changelog/INDEX.md` é gerado.

O orçamento de retomada é **derivado** das referências `F-NNNN`/`ADR-NNNN`
nas entradas do UNRELEASED — sem lista `active_*` hand-maintained.

Fase 1 (aditivo): o módulo coexiste com STATE.md/CHANGELOG.md até a migração
(F-0037). Subcomando: `feat-memory release`.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from feat_memory.memory.schemas import SEMVER_RE
from feat_memory.shared import paths as _paths
from feat_memory.shared.parsing import parse_frontmatter


CHANGELOG_SCHEMA_VERSION = 1
RELEASE_FILE_RE = re.compile(r"^\d+\.\d+\.\d+\.md$")
REF_RE = re.compile(r"\b(F-\d{4}|ADR-\d{4})\b")

INDEX_FOOTER = "_Gerado por `feat-memory release`. Não edite manualmente._"

UNRELEASED_TEMPLATE = """\
---
schema_version: 1
---

# Não-lançado

Trabalho concluído mas ainda não tagueado. Cada entrada referencia as
features e decisões que toca (`F-NNNN` / `ADR-NNNN`); o orçamento de
retomada é derivado dessas referências. Vazio = nada em voo.

## Adicionado

## Mudado

## Corrigido
"""


# --- paths ---------------------------------------------------------------


def changelog_dir(root: Path) -> Path:
    return root / ".feat-memory" / "changelog"


def unreleased_path(root: Path) -> Path:
    return changelog_dir(root) / "UNRELEASED.md"


def index_path(root: Path) -> Path:
    return changelog_dir(root) / "INDEX.md"


def release_path(root: Path, version: str) -> Path:
    return changelog_dir(root) / f"{version}.md"


# --- VERSION -------------------------------------------------------------


def read_version(root: Path) -> str:
    """Lê o arquivo VERSION (fonte do próximo release; __version__ vem do
    metadata do pacote e só reflete após reinstall)."""
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def write_version(root: Path, version: str) -> None:
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")


def _semver_tuple(v: str) -> tuple[int, int, int]:
    core = v[1:] if v.startswith("v") else v
    major, minor, patch = (int(x) for x in core.split("."))
    return major, minor, patch


def is_forward_bump(current: str, target: str) -> bool:
    """True se `target` é estritamente maior que `current` (SemVer)."""
    return _semver_tuple(target) > _semver_tuple(current)


# --- releases / index ----------------------------------------------------


def list_releases(root: Path) -> list[Path]:
    """Arquivos de release ordenados por SemVer ascendente."""
    cdir = changelog_dir(root)
    if not cdir.exists():
        return []
    files = [p for p in cdir.glob("*.md") if RELEASE_FILE_RE.match(p.name)]
    return sorted(files, key=lambda p: _semver_tuple(p.stem))


def _summary_of(body: str) -> str:
    """Primeira linha de prosa do corpo (ignora headings e vazias)."""
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            return s
    return "—"


def gen_changelog_index(root: Path) -> str:
    rows = [
        "# Índice de releases", "",
        "Histórico por tag — um arquivo imutável por versão (ADR-0042).",
        "`UNRELEASED.md` guarda o trabalho ainda não tagueado.", "",
        "| Versão | Data | Resumo |",
        "|---|---|---|",
    ]
    for p in reversed(list_releases(root)):  # mais recente primeiro
        fm, body = parse_frontmatter(p)
        ver = str(fm.get("version", p.stem))
        dt = str(fm.get("date", "—"))
        summary = _summary_of(body).replace("|", "\\|")
        if len(summary) > 80:
            summary = summary[:77] + "..."
        rows.append(f"| {ver} | {dt} | {summary} |")
    rows += ["", INDEX_FOOTER]
    return "\n".join(rows) + "\n"


def write_index(root: Path) -> Path:
    p = index_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(gen_changelog_index(root), encoding="utf-8")
    return p


# --- UNRELEASED / retomada derivada --------------------------------------


def ensure_scaffold(root: Path) -> None:
    """Cria changelog/ + UNRELEASED.md (do template) se ausentes. Idempotente."""
    changelog_dir(root).mkdir(parents=True, exist_ok=True)
    up = unreleased_path(root)
    if not up.exists():
        up.write_text(UNRELEASED_TEMPLATE, encoding="utf-8")


def derive_active_refs(root: Path) -> dict[str, list[str]]:
    """Conjunto ativo derivado das referências no UNRELEASED (ADR-0043).

    Retorna {'features': [...], 'decisions': [...]} — união ordenada dos
    `F-NNNN`/`ADR-NNNN` citados no corpo. Vazio se UNRELEASED não existe ou
    não cita nada (nada em voo).
    """
    up = unreleased_path(root)
    if not up.exists():
        return {"features": [], "decisions": []}
    _, body = parse_frontmatter(up)
    feats, decs = set(), set()
    for line in body.splitlines():
        s = line.lstrip()
        if not (s.startswith("- ") or s.startswith("* ")):
            continue  # só entradas-bullet; prosa não conta como ref ativa
        for token in REF_RE.findall(line):
            (feats if token.startswith("F-") else decs).add(token)
    return {"features": sorted(feats), "decisions": sorted(decs)}


# --- release -------------------------------------------------------------


def freeze_unreleased(root: Path, version: str, on: str) -> Path:
    """Congela UNRELEASED.md em changelog/<version>.md (imutável) e cria um
    UNRELEASED.md novo a partir do template. Regenera o INDEX.

    Não mexe em git nem em VERSION — orquestração fica em `run_release`.
    """
    up = unreleased_path(root)
    _, body = parse_frontmatter(up) if up.exists() else ({}, "")
    body = body.strip("\n")

    target = release_path(root, version)
    if target.exists():
        raise FileExistsError(f"release já existe: {target.name}")

    content = (
        "---\n"
        f"version: {version}\n"
        f"date: {on}\n"
        "---\n\n"
        f"# {version} — {on}\n\n"
        f"{body}\n"
    )
    target.write_text(content, encoding="utf-8")
    up.write_text(UNRELEASED_TEMPLATE, encoding="utf-8")
    write_index(root)
    return target


def run_release(args: argparse.Namespace) -> int:
    _paths._init_paths()
    root = _paths.ROOT
    version = args.version
    if not SEMVER_RE.match(version):
        print(f"Erro: versão inválida '{version}' (esperado X.Y.Z)", file=sys.stderr)
        return 1

    current = read_version(root)
    if not is_forward_bump(current, version):
        print(f"Erro: {version} não é um bump à frente de {current}.", file=sys.stderr)
        return 1

    ensure_scaffold(root)
    active = derive_active_refs(root)
    if not (active["features"] or active["decisions"]) and not args.allow_empty:
        print("Erro: UNRELEASED.md não tem entradas com refs F/ADR. "
              "Use --allow-empty para um release vazio.", file=sys.stderr)
        return 1

    on = args.date or date.today().isoformat()
    try:
        target = freeze_unreleased(root, version, on)
    except FileExistsError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    write_version(root, version)

    rel = target.relative_to(root)
    print(f"✓ release {version} congelado: {rel}")
    print(f"✓ VERSION → {version}; UNRELEASED.md reiniciado; INDEX regenerado")
    print("\nPróximos passos (git ainda manual nesta fase):")
    print("  1. revise o diff")
    print(f"  2. git add -A && git commit -m 'release v{version}'")
    print(f"  3. git tag -a v{version} -m 'v{version}' && git push --follow-tags")
    return 0


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "release",
        help="Congela UNRELEASED.md em changelog/<X.Y.Z>.md, bumpa VERSION "
             "e regenera o INDEX (ADR-0042).",
    )
    p.add_argument("version", help="versão SemVer do release (X.Y.Z)")
    p.add_argument("--date", help="data ISO (default: hoje)")
    p.add_argument("--allow-empty", action="store_true",
                   help="permite release sem entradas no UNRELEASED")
    p.set_defaults(func=run_release)
