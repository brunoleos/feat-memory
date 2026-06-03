"""Testes do cross-check e staleness check do audit (F-0011, ADR-0014)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_memory.governance import audit
from agent_memory.shared import paths as _paths


# A fixture `audit_with_tmp_root` agora vive em conftest.py (compartilhada
# com test_release_status.py — F-0020).


# --- cross-check ---------------------------------------------------------


def test_crosscheck_passes_when_all_ids_resolve(audit_with_tmp_root):
    state_fm = {"active_features": ["F-0001"], "active_decisions": ["ADR-0001"]}
    features = [{"id": "F-0001"}]
    decisions = [{"id": "ADR-0001"}]
    issues = audit.validate_state_crosscheck(state_fm, features, decisions)
    assert issues == []


def test_crosscheck_flags_orphan_feature(audit_with_tmp_root):
    state_fm = {"active_features": ["F-0099"], "active_decisions": []}
    issues = audit.validate_state_crosscheck(state_fm, [], [])
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "F-0099" in issues[0].message
    assert "active_features" in issues[0].message


def test_crosscheck_flags_orphan_decision(audit_with_tmp_root):
    state_fm = {"active_features": [], "active_decisions": ["ADR-0099"]}
    issues = audit.validate_state_crosscheck(state_fm, [], [])
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "ADR-0099" in issues[0].message
    assert "active_decisions" in issues[0].message


def test_crosscheck_resolves_archived_feature_via_merged_list(audit_with_tmp_root):
    """F-0011 A3 + F-0012: a caller (run_audit) passa active+archived
    já mergeados; crosscheck só verifica presença na lista recebida."""
    state_fm = {"active_features": ["F-0099"], "active_decisions": []}
    archived = [{"id": "F-0099"}]
    issues = audit.validate_state_crosscheck(state_fm, archived, [])
    assert issues == []


def test_crosscheck_handles_missing_active_lists(audit_with_tmp_root):
    """STATE.md sem active_features/active_decisions não deve quebrar."""
    issues = audit.validate_state_crosscheck({}, [], [])
    assert issues == []


# --- staleness check -----------------------------------------------------


def _commit(repo: Path, files: dict[str, str], message: str) -> None:
    for relpath, content in files.items():
        full = repo / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", relpath], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message],
                   cwd=repo, check=True)


def test_freshness_no_commits_returns_no_warning(tmp_project):
    issues = audit.validate_state_freshness(tmp_project, days=7)
    assert issues == []


def test_freshness_state_was_touched_returns_no_warning(tmp_project):
    _commit(tmp_project, {"src/foo.py": "x = 1\n"}, "feat: code")
    _commit(tmp_project, {".agent-memory/STATE.md": "# state\n"}, "chore: state")
    issues = audit.validate_state_freshness(tmp_project, days=7)
    assert issues == []


def test_freshness_only_docs_touched_returns_no_warning(tmp_project):
    _commit(tmp_project, {"README.md": "# hi\n"}, "docs: readme")
    _commit(tmp_project, {"docs/guide.md": "# guide\n"}, "docs: guide")
    issues = audit.validate_state_freshness(tmp_project, days=7)
    assert issues == []


def test_freshness_code_touched_no_state_returns_warning(tmp_project):
    _commit(tmp_project, {"src/foo.py": "x = 1\n"}, "feat: code change")
    issues = audit.validate_state_freshness(tmp_project, days=7)
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "STATE.md" in issues[0].artifact
    assert "memory-debrief" in issues[0].message


def test_freshness_no_git_returns_no_warning(tmp_path):
    """tmp_path (sem git init) deve retornar lista vazia, não quebrar."""
    issues = audit.validate_state_freshness(tmp_path, days=7)
    assert issues == []
