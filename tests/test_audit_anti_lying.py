"""Testes do cross-check do audit (F-0011, ADR-0014)."""

from __future__ import annotations

import pytest

from agent_memory import audit


@pytest.fixture
def audit_with_tmp_root(tmp_project, monkeypatch):
    """Aponta os globals de path do módulo audit para tmp_project.

    O audit guarda ROOT/MANIFEST_DIR/etc como módulo-globals porque o
    fluxo normal é via CLI (um processo, um project). Para testes
    unitários precisamos resetar entre execuções.
    """
    monkeypatch.setattr(audit, "ROOT", tmp_project, raising=False)
    monkeypatch.setattr(audit, "AGENT", tmp_project / "AGENT.md", raising=False)
    monkeypatch.setattr(audit, "CLAUDE", tmp_project / "CLAUDE.md", raising=False)
    monkeypatch.setattr(
        audit, "STATE", tmp_project / ".agent-memory" / "STATE.md", raising=False,
    )
    manifest_dir = tmp_project / ".agent-memory" / "manifest"
    decisions_dir = tmp_project / ".agent-memory" / "decisions"
    monkeypatch.setattr(audit, "MANIFEST_DIR", manifest_dir, raising=False)
    monkeypatch.setattr(audit, "FEATURES_DIR", manifest_dir / "features", raising=False)
    monkeypatch.setattr(audit, "DECISIONS_DIR", decisions_dir, raising=False)
    monkeypatch.setattr(audit, "PROPOSALS_DIR", decisions_dir / "proposals", raising=False)
    return tmp_project


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


def test_crosscheck_finds_feature_in_archive(audit_with_tmp_root):
    """F-0011 A3: archive/ conta como localização válida (preview de F-0012)."""
    archive_dir = audit_with_tmp_root / ".agent-memory" / "manifest" / "archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "F-0099-old-feature.md").write_text("---\nid: F-0099\n---\n")

    state_fm = {"active_features": ["F-0099"], "active_decisions": []}
    issues = audit.validate_state_crosscheck(state_fm, [], [])
    assert issues == []


def test_crosscheck_handles_missing_active_lists(audit_with_tmp_root):
    """STATE.md sem active_features/active_decisions não deve quebrar."""
    issues = audit.validate_state_crosscheck({}, [], [])
    assert issues == []
