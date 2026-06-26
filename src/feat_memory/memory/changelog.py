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
import subprocess
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


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    )


def run_release(args: argparse.Namespace) -> int:
    _paths._init_paths()
    root = _paths.ROOT
    # A versão é a do arquivo VERSION (bumpada per-commit, ADR-0020). O
    # release não bumpa: fotografa a versão corrente e a tagueia (ADR-0045).
    version = args.version or read_version(root)
    if not SEMVER_RE.match(version):
        print(f"Erro: versão inválida '{version}' (esperado X.Y.Z)", file=sys.stderr)
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

    rel = target.relative_to(root)
    print(f"✓ release {version} congelado: {rel}; UNRELEASED reiniciado; INDEX regenerado")

    if args.no_commit:
        print("(--no-commit) mutações deixadas no working tree para revisão.")
        return 0

    _git(root, "add", "-A")
    cp = _git(root, "commit", "-m", f"release v{version}")
    if cp.returncode != 0:
        print(f"Erro no commit de release:\n{cp.stderr}", file=sys.stderr)
        return 1
    print("✓ commit de release criado")

    if not args.no_tag:
        cp = _git(root, "tag", "-a", f"v{version}", "-m", f"v{version}")
        if cp.returncode != 0:
            print(f"Erro ao criar a tag v{version}:\n{cp.stderr}", file=sys.stderr)
            return 1
        print(f"✓ tag v{version} criada")

    print("\nPara publicar: git push --follow-tags")
    return 0


# --- migração do layout legado (F-0037, ADR-0042/0043) -------------------


SECTION_RE = re.compile(
    r"^## \[([^\]]+)\](?:\s*-\s*(\d{4}-\d{2}-\d{2}))?\s*$", re.MULTILINE
)


def _split_changelog(text: str) -> list[tuple[str, str | None, str]]:
    """Quebra um CHANGELOG.md monolítico em (label, data, corpo) por seção."""
    matches = list(SECTION_RE.finditer(text))
    out: list[tuple[str, str | None, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1), m.group(2), text[start:end].strip("\n")))
    return out


def _state_active_seed(root: Path) -> str:
    """Bullet com as refs ativas do STATE.md legado, p/ a derivação herdar."""
    state = root / ".feat-memory" / "STATE.md"
    if not state.exists():
        return ""
    try:
        fm, _ = parse_frontmatter(state)
    except ValueError:
        return ""
    refs = list(fm.get("active_features") or []) + list(fm.get("active_decisions") or [])
    if not refs:
        return ""
    return "## Em andamento\n\n- Foco herdado do STATE: " + ", ".join(refs)


def _remove_legacy_state(root: Path) -> None:
    import shutil
    state = root / ".feat-memory" / "STATE.md"
    if state.exists():
        state.unlink()
    cp_dir = root / ".feat-memory" / "checkpoints"
    if cp_dir.exists():
        shutil.rmtree(cp_dir)


def _write_migrated_unreleased(root: Path, unreleased_body: str) -> None:
    seed = _state_active_seed(root)
    body = unreleased_body.strip()
    if not body and not seed:
        unreleased_path(root).write_text(UNRELEASED_TEMPLATE, encoding="utf-8")
        return
    parts = ["---", "schema_version: 1", "---", "", "# Não-lançado", ""]
    if seed:
        parts += [seed, ""]
    if body:
        parts += [body, ""]
    unreleased_path(root).write_text("\n".join(parts) + "\n", encoding="utf-8")


def migrate_to_changelog_folder(root: Path) -> tuple[bool, str]:
    """Migra o layout legado para o novo (F-0037). Idempotente: re-rodar
    num layout já migrado é no-op.

    Split do CHANGELOG.md por versão → changelog/<v>.md; [Unreleased] +
    refs ativas do STATE → UNRELEASED.md; regenera INDEX; remove os legados
    (CHANGELOG.md, STATE.md, checkpoints/).
    """
    if list_releases(root):
        return False, "já migrado (changelog/ já tem releases)"
    changelog_md = root / "CHANGELOG.md"
    state_exists = (root / ".feat-memory" / "STATE.md").exists()
    if not changelog_md.exists() and not state_exists:
        return False, "nada a migrar (sem CHANGELOG.md nem STATE.md)"

    legacy_text = changelog_md.read_text(encoding="utf-8") if changelog_md.exists() else ""
    changelog_dir(root).mkdir(parents=True, exist_ok=True)
    unreleased_body = ""
    n = 0
    for label, dt, body in _split_changelog(legacy_text):
        if label.strip().lower() == "unreleased":
            unreleased_body = body
            continue
        ver = label.strip()
        if not SEMVER_RE.match(ver):
            continue
        date_str = dt or "?"
        content = (f"---\nversion: {ver}\ndate: {date_str}\n---\n\n"
                   f"# {ver} — {date_str}\n\n{body}\n")
        release_path(root, ver).write_text(content, encoding="utf-8")
        n += 1

    _write_migrated_unreleased(root, unreleased_body)
    write_index(root)
    if changelog_md.exists():
        changelog_md.unlink()
    _remove_legacy_state(root)
    return True, f"{n} release(s) migrado(s); UNRELEASED criado; legados removidos"


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "release",
        help="Congela UNRELEASED.md em changelog/<VERSION>.md, commita e cria "
             "a tag v<VERSION> (ADR-0042, ADR-0045). Não bumpa VERSION.",
    )
    p.add_argument("version", nargs="?",
                   help="versão a taguear (default: VERSION atual)")
    p.add_argument("--date", help="data ISO (default: hoje)")
    p.add_argument("--allow-empty", action="store_true",
                   help="permite release sem entradas no UNRELEASED")
    p.add_argument("--no-commit", action="store_true",
                   help="não commita/tagueia; deixa as mutações staged")
    p.add_argument("--no-tag", action="store_true",
                   help="cria o commit de release mas não a tag")
    p.set_defaults(func=run_release)
