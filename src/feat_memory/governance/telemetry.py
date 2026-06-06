"""telemetry.py — Telemetria local opt-out de aderência ao protocolo.

Append-only JSONL em `.feat-memory/.telemetry.jsonl` (gitignored).
Default ligado, kill switch em `.meta.yaml::telemetry_enabled=false`.
Erros silenciosos — telemetria nunca pode quebrar um fluxo do usuário.

Subcomandos:
    feat-memory record EVENT [field=value ...]
    feat-memory log [--since DAYS] [--event NAME] [--json] [--summary]

ADR-0017 e F-0014 cobrem schema, política de privacidade e vocabulário
canônico de eventos.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from feat_memory.shared import paths as _paths
from feat_memory.shared.parsing import read_meta


TELEMETRY_FILENAME = ".telemetry.jsonl"
PRIVACY_HEADER = {
    "_": (
        "feat-memory telemetry — local only, never sent over network. "
        "Disable: .feat-memory/.meta.yaml::telemetry_enabled=false"
    ),
}


def _telemetry_path(root: Path) -> Path:
    return root / ".feat-memory" / TELEMETRY_FILENAME


def _coerce_value(raw: str):
    """Converte string para bool/int/float quando possível, else string."""
    low = raw.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _parse_field_args(pairs: list[str]) -> dict:
    fields: dict = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        fields[key.strip()] = _coerce_value(value)
    return fields


def record(root: Path, event: str, **fields) -> None:
    """Anexa um evento ao JSONL local. Sempre silencioso em erro.

    Respeita `telemetry_enabled: false` em .meta.yaml. Cria o arquivo
    com header de privacidade se ainda não existe.
    """
    try:
        meta = read_meta(root) or {}
        if meta.get("telemetry_enabled") is False:
            return

        path = _telemetry_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)

        is_new = not path.exists()
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "version": meta.get("version"),
            "event": event,
            **fields,
        }

        with path.open("a", encoding="utf-8") as f:
            if is_new:
                f.write(json.dumps(PRIVACY_HEADER) + "\n")
            f.write(json.dumps(entry) + "\n")
    except Exception:
        # Telemetria nunca quebra fluxo. ADR-0017.
        return


def _read_events(root: Path) -> list[dict]:
    path = _telemetry_path(root)
    if not path.exists():
        return []
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "_" in obj and len(obj) == 1:
            continue  # skip privacy header
        events.append(obj)
    return events


def _parse_since(raw: str | None) -> timedelta | None:
    if not raw:
        return None
    raw = raw.strip().lower()
    if raw.endswith("d"):
        return timedelta(days=int(raw[:-1]))
    if raw.endswith("h"):
        return timedelta(hours=int(raw[:-1]))
    return timedelta(days=int(raw))


def _filter_events(events: list[dict],
                   since: timedelta | None,
                   event_name: str | None) -> list[dict]:
    out = events
    if since is not None:
        cutoff = datetime.now(timezone.utc) - since
        out = [e for e in out if _parse_ts(e.get("ts")) and
               _parse_ts(e.get("ts")) >= cutoff]
    if event_name:
        out = [e for e in out if e.get("event") == event_name]
    return out


def _parse_ts(value) -> datetime | None:
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _summarize(events: list[dict]) -> dict:
    counts: dict[str, int] = {}
    sessions_total = 0
    sessions_with_state = 0
    for e in events:
        ev = e.get("event") or "?"
        counts[ev] = counts.get(ev, 0) + 1
        if ev == "session_start":
            sessions_total += 1
            if e.get("state_read") is True:
                sessions_with_state += 1
    adherence = (
        round(sessions_with_state / sessions_total, 2)
        if sessions_total else None
    )
    return {
        "counts": counts,
        "session_start_total": sessions_total,
        "session_start_with_state_read": sessions_with_state,
        "adherence_ratio": adherence,
    }


# --- subparsers / runners ------------------------------------------------


def add_record_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "record",
        help="Anexa um evento à telemetria local (uso por skills)",
    )
    p.add_argument("event", help="nome do evento (ex: session_start)")
    p.add_argument("fields", nargs="*",
                   help="pares key=value adicionais (auto-converte true/false/int)")
    p.set_defaults(func=run_record)


def add_log_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "log",
        help="Lê e agrega .feat-memory/.telemetry.jsonl",
    )
    p.add_argument("--since", metavar="WINDOW",
                   help="filtra por janela recente (ex: 7d, 24h)")
    p.add_argument("--event", metavar="NAME",
                   help="filtra por nome de evento")
    p.add_argument("--json", action="store_true",
                   help="saída JSON (uma linha por evento)")
    p.add_argument("--summary", action="store_true",
                   help="agrega contagens e taxa de adesão")
    p.set_defaults(func=run_log)


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    add_record_subparser(subparsers)
    add_log_subparser(subparsers)


def run_record(args: argparse.Namespace) -> int:
    _paths._init_paths()
    fields = _parse_field_args(getattr(args, "fields", []) or [])
    record(_paths.ROOT, args.event, **fields)
    return 0


def run_log(args: argparse.Namespace) -> int:
    _paths._init_paths()
    events = _read_events(_paths.ROOT)
    events = _filter_events(events, _parse_since(args.since), args.event)

    if args.summary:
        summary = _summarize(events)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("Resumo de telemetria:")
            print(f"  Eventos por tipo:")
            for ev, count in sorted(summary["counts"].items()):
                print(f"    {ev:24s} {count}")
            total = summary["session_start_total"]
            with_state = summary["session_start_with_state_read"]
            ratio = summary["adherence_ratio"]
            ratio_str = f"{ratio:.0%}" if ratio is not None else "—"
            print(f"  session_start: {total} (com STATE.md lido: {with_state}, "
                  f"adesão: {ratio_str})")
        return 0

    if args.json:
        for e in events:
            print(json.dumps(e))
        return 0

    if not events:
        print("Sem eventos registrados.")
        return 0

    print(f"{len(events)} evento(s):")
    for e in reversed(events):  # mais recente primeiro
        ts = e.get("ts", "?")
        ev = e.get("event", "?")
        extras = " ".join(
            f"{k}={v}" for k, v in e.items()
            if k not in ("ts", "event", "version")
        )
        print(f"  {ts}  {ev:24s} {extras}")
    return 0
