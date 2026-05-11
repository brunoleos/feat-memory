"""Testes do `agent-memory archive` (F-0012, ADR-0015)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from agent_memory.governance import audit
from agent_memory.memory import archive
from agent_memory.shared import paths as _paths


# --- helpers -------------------------------------------------------------


def _write_feature(features_dir: Path, fid: str, slug: str, *,
                   status: str, name: str = "feature") -> Path:
    """Escreve um feature card mínimo válido em features_dir."""
    features_dir.mkdir(parents=True, exist_ok=True)
    path = features_dir / f"{fid}-{slug}.md"
    path.write_text(
        f"---\n"
        f"id: {fid}\n"
        f"name: {name}\n"
        f"status: {status}\n"
        f"introduced: 2026-01-01\n"
        f"version: 0.1.0\n"
        f"contracts:\n"
        f"  api: src/foo.py\n"
        f"acceptance:\n"
        f"  - id: A1\n"
        f"    pattern: ubiquitous\n"
        f"    requirement: works\n"
        f"---\n\n# {fid}\n",
        encoding="utf-8",
    )
    return path


def _args(*, apply: bool = False) -> argparse.Namespace:
    return argparse.Namespace(apply=apply, cmd="archive", func=archive.run)


@pytest.fixture
def archive_repo(tmp_project, monkeypatch):
    """Aponta os globals do audit para um tmp repo Git limpo."""
    am = tmp_project / ".agent-memory"
    monkeypatch.setattr(_paths, "ROOT", tmp_project, raising=False)
    monkeypatch.setattr(_paths, "AGENT", tmp_project / "AGENTS.md", raising=False)
    monkeypatch.setattr(_paths, "CLAUDE", tmp_project / "CLAUDE.md", raising=False)
    monkeypatch.setattr(_paths, "STATE", am / "STATE.md", raising=False)
    monkeypatch.setattr(_paths, "MANIFEST_DIR", am / "manifest", raising=False)
    monkeypatch.setattr(
        _paths, "FEATURES_DIR", am / "manifest" / "features", raising=False,
    )
    monkeypatch.setattr(
        _paths, "ARCHIVE_DIR", am / "manifest" / "archive", raising=False,
    )
    monkeypatch.setattr(_paths, "DECISIONS_DIR", am / "decisions", raising=False)
    monkeypatch.setattr(
        _paths, "PROPOSALS_DIR", am / "decisions" / "proposals", raising=False,
    )
    return tmp_project


# --- collect_eligible ----------------------------------------------------


def test_collect_eligible_picks_shipped_not_active(archive_repo):
    feat_dir = _paths.FEATURES_DIR
    _write_feature(feat_dir, "F-0001", "old", status="shipped")
    _write_feature(feat_dir, "F-0002", "wip", status="in_progress")
    _write_feature(feat_dir, "F-0003", "active-shipped", status="shipped")

    state_fm = {"active_features": ["F-0003"]}
    eligible = archive.collect_eligible(feat_dir, state_fm)

    ids = [fm.get("id") for _, fm in eligible]
    assert ids == ["F-0001"]


def test_collect_eligible_active_overrides_shipped(archive_repo):
    """A3: active vence shipped — feature ativa não é elegível."""
    feat_dir = _paths.FEATURES_DIR
    _write_feature(feat_dir, "F-0001", "active", status="shipped")
    state_fm = {"active_features": ["F-0001"]}
    eligible = archive.collect_eligible(feat_dir, state_fm)
    assert eligible == []


def test_collect_eligible_skips_non_shipped(archive_repo):
    feat_dir = _paths.FEATURES_DIR
    _write_feature(feat_dir, "F-0001", "wip", status="in_progress")
    _write_feature(feat_dir, "F-0002", "planned", status="planned")
    _write_feature(feat_dir, "F-0003", "deprecated-feat", status="deprecated")
    eligible = archive.collect_eligible(feat_dir, {"active_features": []})
    assert eligible == []


def test_collect_eligible_handles_missing_dir(tmp_path):
    eligible = archive.collect_eligible(tmp_path / "nope", {})
    assert eligible == []


# --- run dry-run vs apply ------------------------------------------------


def test_run_dry_run_does_not_move(archive_repo, capsys):
    feat_dir = _paths.FEATURES_DIR
    _paths.STATE.parent.mkdir(parents=True, exist_ok=True)
    _paths.STATE.write_text(
        "---\nschema_version: 2\nupdated_at: 2026-05-04T00:00:00Z\n"
        "active_features: []\n---\n", encoding="utf-8",
    )
    _write_feature(feat_dir, "F-0001", "old", status="shipped")

    rc = archive.run(_args(apply=False))
    out = capsys.readouterr().out

    assert rc == 0
    assert "[dry-run]" in out
    assert "F-0001" in out
    assert (feat_dir / "F-0001-old.md").exists()
    assert not (_paths.ARCHIVE_DIR / "F-0001-old.md").exists()


def test_run_apply_moves_via_git_mv(archive_repo, capsys):
    feat_dir = _paths.FEATURES_DIR
    _paths.STATE.parent.mkdir(parents=True, exist_ok=True)
    _paths.STATE.write_text(
        "---\nschema_version: 2\nupdated_at: 2026-05-04T00:00:00Z\n"
        "active_features: []\n---\n", encoding="utf-8",
    )
    _paths.AGENT.write_text(
        "---\nschema_version: 1\nproject: x\nconstraints: []\n"
        "references: {}\nbudgets: {}\n---\n", encoding="utf-8",
    )
    feat_path = _write_feature(feat_dir, "F-0001", "old", status="shipped")
    subprocess.run(["git", "add", "-A"], cwd=archive_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"],
                   cwd=archive_repo, check=True)

    rc = archive.run(_args(apply=True))
    out = capsys.readouterr().out

    assert rc == 0
    assert "git mv" in out
    assert not feat_path.exists()
    assert (_paths.ARCHIVE_DIR / "F-0001-old.md").exists()


def test_run_apply_falls_back_to_fs_when_no_git(tmp_path, monkeypatch):
    """A6: git mv falha (não-tracked / sem git) → shutil.move."""
    am = tmp_path / ".agent-memory"
    monkeypatch.setattr(_paths, "ROOT", tmp_path, raising=False)
    monkeypatch.setattr(_paths, "AGENT", tmp_path / "AGENTS.md", raising=False)
    monkeypatch.setattr(_paths, "CLAUDE", tmp_path / "CLAUDE.md", raising=False)
    monkeypatch.setattr(_paths, "STATE", am / "STATE.md", raising=False)
    monkeypatch.setattr(_paths, "MANIFEST_DIR", am / "manifest", raising=False)
    monkeypatch.setattr(
        _paths, "FEATURES_DIR", am / "manifest" / "features", raising=False,
    )
    monkeypatch.setattr(
        _paths, "ARCHIVE_DIR", am / "manifest" / "archive", raising=False,
    )
    monkeypatch.setattr(_paths, "DECISIONS_DIR", am / "decisions", raising=False)
    monkeypatch.setattr(
        _paths, "PROPOSALS_DIR", am / "decisions" / "proposals", raising=False,
    )

    _paths.STATE.parent.mkdir(parents=True, exist_ok=True)
    _paths.STATE.write_text(
        "---\nschema_version: 2\nupdated_at: 2026-05-04T00:00:00Z\n"
        "active_features: []\n---\n", encoding="utf-8",
    )
    _paths.AGENT.write_text(
        "---\nschema_version: 1\nproject: x\nconstraints: []\n"
        "references: {}\nbudgets: {}\n---\n", encoding="utf-8",
    )
    feat_path = _write_feature(_paths.FEATURES_DIR, "F-0001", "old",
                               status="shipped")

    rc = archive.run(_args(apply=True))
    assert rc == 0
    assert not feat_path.exists()
    assert (_paths.ARCHIVE_DIR / "F-0001-old.md").exists()


# --- audit integration ---------------------------------------------------


def test_audit_scans_archive_dir(archive_repo):
    _paths.STATE.parent.mkdir(parents=True, exist_ok=True)
    _paths.STATE.write_text(
        "---\nschema_version: 2\nupdated_at: 2026-05-04T00:00:00Z\n"
        "active_features: []\n---\n", encoding="utf-8",
    )
    _paths.AGENT.write_text(
        "---\nschema_version: 1\nproject: x\nconstraints: []\n"
        "references: {}\nbudgets: {}\n---\n", encoding="utf-8",
    )
    _write_feature(_paths.FEATURES_DIR, "F-0001", "active",
                   status="in_progress")
    _write_feature(_paths.ARCHIVE_DIR, "F-0099", "old", status="shipped")

    result = audit.run_audit(write_indices=True)

    assert (_paths.ARCHIVE_DIR / "INDEX.md").exists()
    archive_index = (_paths.ARCHIVE_DIR / "INDEX.md").read_text(encoding="utf-8")
    assert "F-0099" in archive_index
    main_index = (_paths.MANIFEST_DIR / "INDEX.md").read_text(encoding="utf-8")
    assert "F-0001" in main_index
    assert "F-0099" not in main_index


def test_audit_crosscheck_resolves_archived_id(archive_repo):
    _paths.STATE.parent.mkdir(parents=True, exist_ok=True)
    _paths.STATE.write_text(
        "---\nschema_version: 2\nupdated_at: 2026-05-04T00:00:00Z\n"
        "active_features: [F-0099]\n---\n", encoding="utf-8",
    )
    _paths.AGENT.write_text(
        "---\nschema_version: 1\nproject: x\nconstraints: []\n"
        "references: {}\nbudgets: {}\n---\n", encoding="utf-8",
    )
    _write_feature(_paths.ARCHIVE_DIR, "F-0099", "old", status="shipped")

    result = audit.run_audit(write_indices=False)
    errors = [i for i in result["issues"] if i["severity"] == "error"]
    crosscheck_errors = [
        e for e in errors if "F-0099" in e["message"] and "active_features" in e["message"]
    ]
    assert crosscheck_errors == []


# --- CLI surface ---------------------------------------------------------


def test_archive_subcommand_registered(capsys):
    from agent_memory import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["archive", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--apply" in out
