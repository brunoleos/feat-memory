"""Fixtures compartilhadas pelos testes."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Cria um diretório temporário inicializado como repositório Git.

    Suficiente para testar deploy e auditoria. O usuário/email são
    configurados localmente para que `git commit` funcione se o teste
    precisar.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, check=True,
    )
    return tmp_path


@pytest.fixture
def audit_with_tmp_root(tmp_project, monkeypatch):
    """Aponta os globals de path (agent_memory.shared.paths) para tmp_project.

    Compartilhada por testes de audit/crosscheck (F-0011) e
    release-status (F-0020). Resetada entre execuções via monkeypatch.
    """
    from agent_memory.shared import paths as _paths

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
    monkeypatch.setattr(_paths, "SUPERSEDED_DIR", decisions_dir / "superseded", raising=False)
    monkeypatch.setattr(_paths, "PROPOSALS_DIR", decisions_dir / "proposals", raising=False)
    return tmp_project
