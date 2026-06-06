"""checkpoints.py — STATE.md como view de checkpoints append-only.

Cada invocação de `memory-debrief` (ou `feat-memory checkpoint` direto)
cria um arquivo imutável em `.feat-memory/checkpoints/YYYY-MM-DD-HHMMSS.md`.
`STATE.md` é regerado a partir dos checkpoints; mesmo schema do legado,
contrato com `memory-bootstrap` preservado (Liskov-safe).

Subcomandos:
    feat-memory checkpoint --summary "..." [--current ...] [--next ...]
                            [--features F-...,F-...] [--decisions ADR-...,...]
                            [--blocked-on "..."] [--author NAME]
    feat-memory state-rebuild

ADR-0018 explica o modelo append-only e a inversão STATE→view.
ADR-0019 detalha o schema do checkpoint, convenção de nomes e migração.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from feat_memory.shared import paths as _paths
from feat_memory.shared.parsing import parse_frontmatter, read_meta


CHECKPOINT_SCHEMA_VERSION = 1
STATE_SCHEMA_VERSION = 2
DEFAULT_STATE_VIEW_WINDOW = 1
DEFAULT_RECENT_ROWS = 5
DEFAULT_AUTHOR = "feat-memory"


# --- helpers -------------------------------------------------------------


def _checkpoints_dir(root: Path) -> Path:
    return root / ".feat-memory" / "checkpoints"


def _state_path(root: Path) -> Path:
    return root / ".feat-memory" / "STATE.md"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ts_for_filename(dt: datetime) -> str:
    """ISO compacto para nome de arquivo (sortable lex == sortable temporal)."""
    return dt.strftime("%Y-%m-%d-%H%M%S")


def _ts_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _state_view_window(root: Path) -> int:
    meta = read_meta(root) or {}
    raw = meta.get("state_view_window", DEFAULT_STATE_VIEW_WINDOW)
    try:
        n = int(raw)
        return n if n > 0 else DEFAULT_STATE_VIEW_WINDOW
    except (TypeError, ValueError):
        return DEFAULT_STATE_VIEW_WINDOW


def list_checkpoints(root: Path) -> list[Path]:
    """Retorna paths ordenados ascendente por nome (= por timestamp)."""
    cp_dir = _checkpoints_dir(root)
    if not cp_dir.exists():
        return []
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}(-\d+)?\.md$")
    return sorted(p for p in cp_dir.glob("*.md") if pattern.match(p.name))


def load_checkpoint(path: Path) -> tuple[dict, str]:
    """Frontmatter + body do checkpoint."""
    return parse_frontmatter(path)


# --- append --------------------------------------------------------------


def _resolve_filename(cp_dir: Path, dt: datetime) -> Path:
    """Nome único; sufixa com -N se já houver colisão de timestamp."""
    base = _ts_for_filename(dt)
    candidate = cp_dir / f"{base}.md"
    if not candidate.exists():
        return candidate
    n = 1
    while True:
        candidate = cp_dir / f"{base}-{n}.md"
        if not candidate.exists():
            return candidate
        n += 1


def append_checkpoint(root: Path, *,
                      summary: str,
                      current: str | None = None,
                      next_: str | None = None,
                      features: list[str] | None = None,
                      decisions: list[str] | None = None,
                      blocked_on: str | None = None,
                      author: str | None = None,
                      body: str = "",
                      now: datetime | None = None) -> Path:
    """Grava um novo checkpoint imutável e retorna seu path.

    Defaults para current/next/features/decisions/blocked_on são puxados
    do checkpoint mais recente (continuidade trivial — agente só especifica
    o que mudou). Se não há checkpoint anterior, defaults sensatos
    (`current = summary`, `next = "TODO"`).
    """
    import yaml

    cp_dir = _checkpoints_dir(root)
    cp_dir.mkdir(parents=True, exist_ok=True)

    prior = list_checkpoints(root)
    prior_fm: dict = {}
    if prior:
        prior_fm, _ = load_checkpoint(prior[-1])

    if current is None:
        current = summary
    if next_ is None:
        next_ = prior_fm.get("next") or "TODO"
    if features is None:
        features = list(prior_fm.get("active_features") or [])
    if decisions is None:
        decisions = list(prior_fm.get("active_decisions") or [])
    if blocked_on is None:
        blocked_on = prior_fm.get("blocked_on")
    if author is None:
        author = DEFAULT_AUTHOR

    dt = now or _now_utc()
    fm = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "ts": _ts_iso(dt),
        "author": author,
        "active_features": features,
        "active_decisions": decisions,
        "blocked_on": blocked_on,
        "current": current,
        "next": next_,
        "summary": summary,
    }

    path = _resolve_filename(cp_dir, dt)
    body_part = f"\n{body}\n" if body.strip() else "\n"
    content = (
        "---\n"
        + yaml.safe_dump(fm, sort_keys=False, default_flow_style=False,
                         allow_unicode=True)
        + "---\n"
        + body_part
    )
    path.write_text(content, encoding="utf-8")
    return path


# --- render --------------------------------------------------------------


def render_state(root: Path,
                 window: int | None = None,
                 recent_rows: int = DEFAULT_RECENT_ROWS) -> str:
    """Gera o conteúdo de STATE.md a partir dos checkpoints.

    `window` checkpoints mais recentes alimentam Current/Next/active_*.
    `recent_rows` dos anteriores alimentam a tabela Recent.
    """
    import yaml

    if window is None:
        window = _state_view_window(root)

    checkpoints = list_checkpoints(root)
    if not checkpoints:
        return _empty_state()

    head = checkpoints[-window:]
    head_fm: list[dict] = []
    for p in head:
        fm, _ = load_checkpoint(p)
        head_fm.append(fm)
    latest = head_fm[-1]

    fm_out = {
        "schema_version": STATE_SCHEMA_VERSION,
        "updated_at": latest.get("ts"),
        "updated_by": latest.get("author"),
        "active_features": latest.get("active_features") or [],
        "active_decisions": latest.get("active_decisions") or [],
        "blocked_on": latest.get("blocked_on"),
    }

    if window > 1:
        currents = [c.get("current", "") for c in head_fm if c.get("current")]
        nexts = [c.get("next", "") for c in head_fm if c.get("next")]
        current_text = "\n".join(f"- {x}" for x in currents)
        next_text = "\n".join(f"- {x}" for x in nexts)
    else:
        current_text = latest.get("current", "")
        next_text = latest.get("next", "")

    recent = checkpoints[:-window][-recent_rows:]
    recent_table = _render_recent(recent)

    body = (
        "# Estado\n\n"
        "## Current\n\n"
        f"{current_text}\n\n"
        "## Next\n\n"
        f"{next_text}\n\n"
        "## Recent\n\n"
        f"{recent_table}"
    )

    return (
        "---\n"
        + yaml.safe_dump(fm_out, sort_keys=False, default_flow_style=False,
                         allow_unicode=True)
        + "---\n\n"
        + body
    )


def _render_recent(checkpoints: list[Path]) -> str:
    if not checkpoints:
        return "_(sem checkpoints anteriores)_\n"
    rows = [
        "| ts | author | features tocadas | summary |",
        "| --- | --- | --- | --- |",
    ]
    for p in reversed(checkpoints):  # mais recente primeiro
        fm, _ = load_checkpoint(p)
        ts = str(fm.get("ts", "?"))[:19]  # corta segundos finos / tz
        author = str(fm.get("author", "?"))
        feats = ",".join(fm.get("active_features") or []) or "—"
        summary = str(fm.get("summary", "")).replace("\n", " ").replace("|", "\\|")
        if len(summary) > 80:
            summary = summary[:77] + "..."
        rows.append(f"| {ts} | {author} | {feats} | {summary} |")
    return "\n".join(rows) + "\n"


def _empty_state() -> str:
    """STATE.md mínimo quando não há checkpoints (greenfield)."""
    return (
        "---\n"
        f"schema_version: {STATE_SCHEMA_VERSION}\n"
        f"updated_at: {_ts_iso(_now_utc())}\n"
        "updated_by: feat-memory\n"
        "active_features: []\n"
        "active_decisions: []\n"
        "blocked_on: null\n"
        "---\n\n"
        "# Estado\n\n"
        "## Current\n\n"
        "_(nenhum checkpoint registrado ainda. Rode "
        "`feat-memory checkpoint --summary '...'` ou ative a skill "
        "`memory-debrief`)_\n\n"
        "## Next\n\n"
        "TODO\n\n"
        "## Recent\n\n"
        "_(sem checkpoints anteriores)_\n"
    )


def write_state(root: Path) -> Path:
    """Renderiza e grava STATE.md. Retorna o path."""
    content = render_state(root)
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# --- subparsers / runners ------------------------------------------------


def add_checkpoint_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "checkpoint",
        help="Anexa novo checkpoint ao .feat-memory/checkpoints/ e "
             "regera STATE.md (F-0015, ADR-0018)",
    )
    p.add_argument("--summary", required=True,
                   help="resumo do estado da sessão (1-3 frases)")
    p.add_argument("--current",
                   help="linha resumo do foco atual (default: igual ao summary)")
    p.add_argument("--next", dest="next_",
                   help="próxima ação concreta (default: herda do anterior)")
    p.add_argument("--features", default=None,
                   help="lista CSV de F-NNNN (default: herda do anterior)")
    p.add_argument("--decisions", default=None,
                   help="lista CSV de ADR-NNNN (default: herda do anterior)")
    p.add_argument("--blocked-on", default=None,
                   help="bloqueio externo (default: herda do anterior)")
    p.add_argument("--author", default=None,
                   help="identificação do agente (default: feat-memory)")
    p.set_defaults(func=run_checkpoint)


def add_state_rebuild_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "state-rebuild",
        help="Regera STATE.md a partir dos checkpoints (recovery, sem "
             "criar novo checkpoint)",
    )
    p.set_defaults(func=run_state_rebuild)


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    add_checkpoint_subparser(subparsers)
    add_state_rebuild_subparser(subparsers)


def _features_arg(raw: str | None, fallback: object) -> list[str] | None:
    if raw is None:
        return None  # signal "use default from prior"
    return _parse_csv(raw)


def run_checkpoint(args: argparse.Namespace) -> int:
    _paths._init_paths()
    features = _features_arg(args.features, None) if args.features is not None else None
    decisions = _parse_csv(args.decisions) if args.decisions is not None else None

    cp_path = append_checkpoint(
        _paths.ROOT,
        summary=args.summary,
        current=args.current,
        next_=args.next_,
        features=features,
        decisions=decisions,
        blocked_on=args.blocked_on,
        author=args.author,
    )
    state_path = write_state(_paths.ROOT)
    rel_cp = cp_path.relative_to(_paths.ROOT)
    rel_st = state_path.relative_to(_paths.ROOT)
    print(f"✓ checkpoint gravado: {rel_cp}")
    print(f"✓ STATE.md regerado:  {rel_st}")
    return 0


def run_state_rebuild(args: argparse.Namespace) -> int:
    _paths._init_paths()
    checkpoints = list_checkpoints(_paths.ROOT)
    if not checkpoints:
        print("Nenhum checkpoint encontrado em .feat-memory/checkpoints/.",
              file=sys.stderr)
        print("Rode `feat-memory checkpoint --summary '...'` para criar o primeiro,",
              file=sys.stderr)
        print("ou `feat-memory migrate --to=checkpoints` para migrar de STATE.md legado.",
              file=sys.stderr)
        return 1
    state_path = write_state(_paths.ROOT)
    rel_st = state_path.relative_to(_paths.ROOT)
    print(f"✓ STATE.md regerado a partir de {len(checkpoints)} checkpoint(s): {rel_st}")
    return 0
