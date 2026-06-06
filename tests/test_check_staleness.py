"""Testes do `feat-memory check-staleness-staged` (F-0013, ADR-0016)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from feat_memory.governance import audit, check_staleness
from feat_memory.shared import paths as _paths


# --- helpers -------------------------------------------------------------


def _stage(repo: Path, files: dict[str, str]) -> None:
    for relpath, content in files.items():
        full = repo / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", relpath], cwd=repo, check=True)


# --- staged_warning core ------------------------------------------------


def test_staged_warning_returns_text_when_code_no_state(tmp_project):
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})
    msg = check_staleness.staged_warning(tmp_project)
    assert msg is not None
    assert "STATE.md" in msg
    assert "memory-debrief" in msg


def test_staged_warning_silent_when_state_in_staging(tmp_project):
    _stage(tmp_project, {
        "src/foo.py": "x = 1\n",
        ".feat-memory/STATE.md": "# state\n",
    })
    msg = check_staleness.staged_warning(tmp_project)
    assert msg is None


def test_staged_warning_silent_when_only_noncode_staged(tmp_project):
    _stage(tmp_project, {
        "README.md": "# hi\n",
        "docs/guide.md": "# guide\n",
        "tests/test_foo.py": "def test(): pass\n",
        ".feat-memory/manifest/features/F-0099-foo.md": "---\nid: F-0099\n---\n",
    })
    msg = check_staleness.staged_warning(tmp_project)
    assert msg is None


def test_staged_warning_silent_when_nothing_staged(tmp_project):
    msg = check_staleness.staged_warning(tmp_project)
    assert msg is None


def test_staged_warning_silent_when_not_a_git_repo(tmp_path):
    """A6: fail-soft — sem git, retorna None sem quebrar."""
    msg = check_staleness.staged_warning(tmp_path)
    assert msg is None


# --- run() exit code and stderr surface ----------------------------------


def test_run_always_exits_zero_with_warning(tmp_project, capsys, monkeypatch):
    """A4: soft sempre — exit 0 mesmo emitindo aviso."""
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})

    rc = check_staleness.run(argparse.Namespace())

    assert rc == 0
    err = capsys.readouterr().err
    assert "memory-debrief" in err
    assert "⚠" in err


def test_run_exits_zero_silent_when_clean(tmp_project, capsys, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)
    _stage(tmp_project, {".feat-memory/STATE.md": "# state\n"})

    rc = check_staleness.run(argparse.Namespace())

    assert rc == 0
    err = capsys.readouterr().err
    assert "memory-debrief" not in err
    assert err == ""


# --- CLI surface ---------------------------------------------------------


def test_subcommand_registered(capsys):
    from feat_memory import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "check-staleness-staged" in out
