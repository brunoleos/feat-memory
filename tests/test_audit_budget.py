"""Testes do warning de custo de retomada (F-0019)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_memory.governance import audit
from agent_memory.shared import paths as _paths


@pytest.fixture
def audit_with_tmp_root(tmp_project, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", tmp_project, raising=False)
    monkeypatch.setattr(_paths, "AGENT", tmp_project / "AGENTS.md", raising=False)
    monkeypatch.setattr(_paths, "CLAUDE", tmp_project / "CLAUDE.md", raising=False)
    monkeypatch.setattr(
        _paths, "STATE", tmp_project / ".agent-memory" / "STATE.md", raising=False,
    )
    manifest_dir = tmp_project / ".agent-memory" / "manifest"
    decisions_dir = tmp_project / ".agent-memory" / "decisions"
    monkeypatch.setattr(_paths, "MANIFEST_DIR", manifest_dir, raising=False)
    monkeypatch.setattr(_paths, "FEATURES_DIR", manifest_dir / "features", raising=False)
    monkeypatch.setattr(_paths, "ARCHIVE_DIR", manifest_dir / "archive", raising=False)
    monkeypatch.setattr(_paths, "DECISIONS_DIR", decisions_dir, raising=False)
    monkeypatch.setattr(_paths, "PROPOSALS_DIR", decisions_dir / "proposals", raising=False)
    return tmp_project


def test_validate_resumption_budget_within_limit_returns_no_issue():
    issues = audit.validate_resumption_budget(cost=8000, max_bytes=12288)
    assert issues == []


def test_validate_resumption_budget_at_limit_returns_no_issue():
    """Limite exato não dispara — só estritamente maior."""
    issues = audit.validate_resumption_budget(cost=12288, max_bytes=12288)
    assert issues == []


def test_validate_resumption_budget_over_limit_returns_warning():
    issues = audit.validate_resumption_budget(cost=22437, max_bytes=12288)
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert issues[0].artifact == "AGENTS.md"
    assert "22,437" in issues[0].message
    assert "12,288" in issues[0].message
    assert "agent-memory archive" in issues[0].message


def test_compute_resumption_cost_sums_all_bootstrap_files(audit_with_tmp_root):
    """Cost = AGENTS + CLAUDE + STATE + manifest INDEX + decisions INDEX."""
    root = audit_with_tmp_root
    (root / "AGENTS.md").write_text("a" * 100, encoding="utf-8")
    (root / "CLAUDE.md").write_text("c" * 50, encoding="utf-8")
    (root / ".agent-memory").mkdir()
    (root / ".agent-memory" / "STATE.md").write_text("s" * 200, encoding="utf-8")
    (root / ".agent-memory" / "manifest").mkdir()
    (root / ".agent-memory" / "manifest" / "INDEX.md").write_text(
        "m" * 75, encoding="utf-8",
    )
    (root / ".agent-memory" / "decisions").mkdir()
    (root / ".agent-memory" / "decisions" / "INDEX.md").write_text(
        "d" * 25, encoding="utf-8",
    )

    cost = audit._compute_resumption_cost()
    assert cost == 100 + 50 + 200 + 75 + 25


def test_compute_resumption_cost_handles_missing_files(audit_with_tmp_root):
    """Arquivos ausentes não devem quebrar — soma só o que existe."""
    root = audit_with_tmp_root
    (root / "AGENTS.md").write_text("a" * 100, encoding="utf-8")
    cost = audit._compute_resumption_cost()
    assert cost == 100
