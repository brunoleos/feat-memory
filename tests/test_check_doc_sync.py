"""Testes do `feat-memory check-doc-sync-staged` — gate hard de drift (B1).

Diferença do `check-staleness-staged` (soft, só STATE): este BLOQUEIA (exit 1)
quando há código staged sem que NENHUM artefato de doc — STATE.md, manifest/**
ou decisions/** — esteja no mesmo staging.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from feat_memory.governance import check_doc_sync
from feat_memory.shared import paths as _paths


# --- helpers -------------------------------------------------------------


def _stage(repo: Path, files: dict[str, str]) -> None:
    for relpath, content in files.items():
        full = repo / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", relpath], cwd=repo, check=True)


# --- staged_block_reason core -------------------------------------------


def test_blocks_when_code_without_any_doc(tmp_project):
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})
    reason = check_doc_sync.staged_block_reason(tmp_project)
    assert reason is not None
    assert ".feat-memory" in reason


def test_silent_when_state_staged(tmp_project):
    _stage(tmp_project, {
        "src/foo.py": "x = 1\n",
        ".feat-memory/STATE.md": "# state\n",
    })
    assert check_doc_sync.staged_block_reason(tmp_project) is None


def test_silent_when_manifest_staged(tmp_project):
    """Extensão-chave sobre o soft: manifest satisfaz o gate, sem STATE."""
    _stage(tmp_project, {
        "src/foo.py": "x = 1\n",
        ".feat-memory/manifest/features/F-0099-foo.md": "---\nid: F-0099\n---\n",
    })
    assert check_doc_sync.staged_block_reason(tmp_project) is None


def test_silent_when_decision_staged(tmp_project):
    _stage(tmp_project, {
        "src/foo.py": "x = 1\n",
        ".feat-memory/decisions/0099-foo.md": "---\nid: ADR-0099\n---\n",
    })
    assert check_doc_sync.staged_block_reason(tmp_project) is None


def test_silent_when_only_noncode_staged(tmp_project):
    """README/docs/tests não são código → nada a bloquear."""
    _stage(tmp_project, {
        "README.md": "# hi\n",
        "docs/guide.md": "# guide\n",
        "tests/test_foo.py": "def test(): pass\n",
    })
    assert check_doc_sync.staged_block_reason(tmp_project) is None


def test_silent_when_nothing_staged(tmp_project):
    assert check_doc_sync.staged_block_reason(tmp_project) is None


def test_silent_when_not_a_git_repo(tmp_path):
    """Fail-soft: sem git, não bloqueia (a fail-open de binário é no hook)."""
    assert check_doc_sync.staged_block_reason(tmp_path) is None


# --- run() exit code and stderr surface ----------------------------------


def test_run_exits_one_and_warns_when_blocking(tmp_project, capsys, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})

    rc = check_doc_sync.run(argparse.Namespace())

    assert rc == 1
    err = capsys.readouterr().err
    assert ".feat-memory" in err


def test_run_exits_zero_silent_when_doc_synced(tmp_project, capsys, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)
    _stage(tmp_project, {
        "src/foo.py": "x = 1\n",
        ".feat-memory/manifest/features/F-0099-foo.md": "---\nid: F-0099\n---\n",
    })

    rc = check_doc_sync.run(argparse.Namespace())

    assert rc == 0
    assert capsys.readouterr().err == ""


# --- CLI surface ---------------------------------------------------------


def test_subcommand_registered(capsys):
    from feat_memory import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "check-doc-sync-staged" in out
