"""Testes de F-0014 / ADR-0017: telemetria local opt-out."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from feat_memory.governance import audit, telemetry
from feat_memory.shared import paths as _paths


# --- helpers -------------------------------------------------------------


def _seed_meta(root: Path, *, telemetry_enabled: bool = True,
               version: str = "0.6.0") -> None:
    am = root / ".feat-memory"
    am.mkdir(parents=True, exist_ok=True)
    (am / ".meta.yaml").write_text(
        f"schema_version: 1\n"
        f"version: {version}\n"
        f"deployed_at: 2026-05-04T00:00:00+00:00\n"
        f"cli_path: /tmp/feat-memory\n"
        f"telemetry_enabled: {'true' if telemetry_enabled else 'false'}\n",
        encoding="utf-8",
    )


@pytest.fixture
def telemetry_root(tmp_path):
    _seed_meta(tmp_path)
    return tmp_path


# --- record() ------------------------------------------------------------


def test_record_appends_event_to_jsonl(telemetry_root):
    telemetry.record(telemetry_root, "session_start", state_read=True)

    path = telemetry_root / ".feat-memory" / ".telemetry.jsonl"
    assert path.exists()

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # header + 1 event
    header = json.loads(lines[0])
    assert "_" in header
    event = json.loads(lines[1])
    assert event["event"] == "session_start"
    assert event["state_read"] is True
    assert event["version"] == "0.6.0"
    assert "ts" in event


def test_record_respects_telemetry_disabled(tmp_path):
    _seed_meta(tmp_path, telemetry_enabled=False)
    telemetry.record(tmp_path, "session_start", state_read=True)
    path = tmp_path / ".feat-memory" / ".telemetry.jsonl"
    assert not path.exists()


def test_record_works_without_meta_yaml(tmp_path):
    """A6 + ADR-0013: tolera consumidor pré-v0.6 sem .meta.yaml."""
    (tmp_path / ".feat-memory").mkdir()
    telemetry.record(tmp_path, "session_start")
    path = tmp_path / ".feat-memory" / ".telemetry.jsonl"
    assert path.exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[-1])
    assert event["event"] == "session_start"
    assert event["version"] is None


def test_record_is_silent_on_error(monkeypatch, tmp_path):
    """A6: telemetria nunca quebra fluxo do usuário."""
    def boom(*a, **k):
        raise RuntimeError("disk full")
    monkeypatch.setattr("pathlib.Path.open", boom, raising=False)
    # Não deve levantar exceção mesmo se I/O explode
    telemetry.record(tmp_path, "session_start")


def test_record_appends_multiple_events(telemetry_root):
    telemetry.record(telemetry_root, "session_start", state_read=True)
    telemetry.record(telemetry_root, "debrief_run", features="F-0010")

    path = telemetry_root / ".feat-memory" / ".telemetry.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3  # header + 2 events
    e1 = json.loads(lines[1])
    e2 = json.loads(lines[2])
    assert e1["event"] == "session_start"
    assert e2["event"] == "debrief_run"


# --- field coercion ------------------------------------------------------


def test_coerce_value_handles_basic_types():
    assert telemetry._coerce_value("true") is True
    assert telemetry._coerce_value("False") is False
    assert telemetry._coerce_value("null") is None
    assert telemetry._coerce_value("42") == 42
    assert telemetry._coerce_value("3.14") == 3.14
    assert telemetry._coerce_value("hello") == "hello"


def test_parse_field_args():
    fields = telemetry._parse_field_args([
        "state_read=true", "count=5", "name=foo", "ratio=0.75",
    ])
    assert fields == {
        "state_read": True, "count": 5, "name": "foo", "ratio": 0.75,
    }


def test_parse_field_args_skips_invalid():
    fields = telemetry._parse_field_args(["valid=1", "invalid"])
    assert fields == {"valid": 1}


# --- run_record CLI ------------------------------------------------------


def test_run_record_writes_event_via_args(telemetry_root, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(telemetry_root)
    args = argparse.Namespace(
        event="session_start",
        fields=["state_read=true", "branch=main"],
        cmd="record",
    )
    rc = telemetry.run_record(args)
    assert rc == 0

    events = telemetry._read_events(telemetry_root)
    assert len(events) == 1
    assert events[0]["event"] == "session_start"
    assert events[0]["state_read"] is True
    assert events[0]["branch"] == "main"


# --- _read_events / log filtering ----------------------------------------


def test_read_events_skips_privacy_header(telemetry_root):
    telemetry.record(telemetry_root, "session_start")
    events = telemetry._read_events(telemetry_root)
    assert len(events) == 1
    assert "_" not in events[0]


def test_read_events_handles_missing_file(tmp_path):
    assert telemetry._read_events(tmp_path) == []


def test_read_events_skips_corrupt_lines(telemetry_root):
    telemetry.record(telemetry_root, "session_start")
    path = telemetry_root / ".feat-memory" / ".telemetry.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write("this is not json\n")
    telemetry.record(telemetry_root, "debrief_run")

    events = telemetry._read_events(telemetry_root)
    assert len(events) == 2
    assert events[0]["event"] == "session_start"
    assert events[1]["event"] == "debrief_run"


def test_filter_by_event(telemetry_root):
    telemetry.record(telemetry_root, "session_start")
    telemetry.record(telemetry_root, "debrief_run")
    telemetry.record(telemetry_root, "session_start")

    events = telemetry._read_events(telemetry_root)
    filtered = telemetry._filter_events(events, None, "session_start")
    assert len(filtered) == 2
    assert all(e["event"] == "session_start" for e in filtered)


def test_filter_by_since_window(telemetry_root):
    """Eventos antigos (mock manual) são filtrados pela janela."""
    path = telemetry_root / ".feat-memory" / ".telemetry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)

    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(timespec="seconds")
    new = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(
        json.dumps({"_": "header"}) + "\n"
        + json.dumps({"ts": old, "event": "ancient"}) + "\n"
        + json.dumps({"ts": new, "event": "fresh"}) + "\n",
        encoding="utf-8",
    )

    events = telemetry._read_events(telemetry_root)
    filtered = telemetry._filter_events(events, timedelta(days=7), None)
    assert [e["event"] for e in filtered] == ["fresh"]


def test_parse_since_formats():
    assert telemetry._parse_since("7d") == timedelta(days=7)
    assert telemetry._parse_since("24h") == timedelta(hours=24)
    assert telemetry._parse_since("3") == timedelta(days=3)
    assert telemetry._parse_since(None) is None


# --- _summarize ----------------------------------------------------------


def test_summarize_computes_adherence_ratio(telemetry_root):
    telemetry.record(telemetry_root, "session_start", state_read=True)
    telemetry.record(telemetry_root, "session_start", state_read=False)
    telemetry.record(telemetry_root, "session_start", state_read=True)
    telemetry.record(telemetry_root, "debrief_run")

    events = telemetry._read_events(telemetry_root)
    summary = telemetry._summarize(events)
    assert summary["counts"] == {"session_start": 3, "debrief_run": 1}
    assert summary["session_start_total"] == 3
    assert summary["session_start_with_state_read"] == 2
    assert summary["adherence_ratio"] == 0.67


def test_summarize_handles_empty():
    summary = telemetry._summarize([])
    assert summary["counts"] == {}
    assert summary["adherence_ratio"] is None


# --- run_log surface ----------------------------------------------------


def test_run_log_summary_outputs_human_format(telemetry_root, capsys, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(telemetry_root)
    telemetry.record(telemetry_root, "session_start", state_read=True)

    args = argparse.Namespace(
        since=None, event=None, json=False, summary=True, cmd="log",
    )
    rc = telemetry.run_log(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Resumo de telemetria" in out
    assert "session_start" in out
    assert "adesão" in out


def test_run_log_json_outputs_per_line(telemetry_root, capsys, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(telemetry_root)
    telemetry.record(telemetry_root, "session_start", state_read=True)
    telemetry.record(telemetry_root, "debrief_run")

    args = argparse.Namespace(
        since=None, event=None, json=True, summary=False, cmd="log",
    )
    rc = telemetry.run_log(args)
    out = capsys.readouterr().out
    assert rc == 0
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 2
    parsed = [json.loads(l) for l in lines]
    assert parsed[0]["event"] == "session_start"
    assert parsed[1]["event"] == "debrief_run"


def test_run_log_empty_state(telemetry_root, capsys, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(telemetry_root)

    args = argparse.Namespace(
        since=None, event=None, json=False, summary=False, cmd="log",
    )
    rc = telemetry.run_log(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Sem eventos" in out


# --- gitignore template integration -------------------------------------


def test_deploy_adds_telemetry_jsonl_to_gitignore(tmp_project):
    from feat_memory import deploy
    deploy.ensure_gitignore(tmp_project)
    gitignore = (tmp_project / ".gitignore").read_text(encoding="utf-8")
    assert ".feat-memory/.telemetry.jsonl" in gitignore


# --- CLI surface --------------------------------------------------------


def test_record_subcommand_registered(capsys):
    from feat_memory import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "record" in out
    assert "log" in out
