"""Testes do cross-check status-vs-release do audit (F-0020, ADR-0024)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from feat_memory.governance import audit


# --- validate_release_status (unitário) ----------------------------------


def test_in_progress_feature_with_released_version_warns():
    features = [{"id": "F-0010", "status": "in_progress", "version": "0.6.0"}]
    issues = audit.validate_release_status(features, {"0.6.0"})
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "F-0010" in issues[0].message
    assert "0.6.0" in issues[0].message


def test_shipped_feature_never_warns():
    features = [{"id": "F-0010", "status": "shipped", "version": "0.6.0"}]
    assert audit.validate_release_status(features, {"0.6.0"}) == []


def test_in_progress_with_unreleased_version_is_fine():
    """Feature em desenvolvimento para a próxima release não é drift."""
    features = [{"id": "F-0020", "status": "in_progress", "version": "0.10.0"}]
    assert audit.validate_release_status(features, {"0.6.0", "0.9.0"}) == []


def test_missing_version_is_tolerated():
    features = [{"id": "F-0010", "status": "in_progress"}]
    assert audit.validate_release_status(features, {"0.6.0"}) == []


def test_no_released_versions_is_failsoft():
    """Sem CHANGELOG/tags conhecidos, não inventa sinal."""
    features = [{"id": "F-0010", "status": "in_progress", "version": "0.6.0"}]
    assert audit.validate_release_status(features, set()) == []


# --- released_versions (derivação de CHANGELOG + tags) -------------------


def test_released_versions_reads_changelog(tmp_path: Path):
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [0.9.0] - 2026-05-11\n\n"
        "## [0.8.1] - 2026-05-10\n",
        encoding="utf-8",
    )
    versions = audit.released_versions(tmp_path)
    assert "0.9.0" in versions
    assert "0.8.1" in versions
    # [Unreleased] não casa o padrão numérico.
    assert "Unreleased" not in versions


def test_released_versions_reads_git_tags(tmp_project: Path):
    (tmp_project / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_project, check=True)
    subprocess.run(["git", "tag", "v0.4.0"], cwd=tmp_project, check=True)
    subprocess.run(["git", "tag", "sandbox"], cwd=tmp_project, check=True)  # ignorada
    versions = audit.released_versions(tmp_project)
    assert "0.4.0" in versions
    assert "sandbox" not in versions


def test_released_versions_failsoft_without_sources(tmp_path: Path):
    """Sem CHANGELOG e sem git, retorna set vazio em vez de quebrar."""
    assert audit.released_versions(tmp_path) == set()


# --- end-to-end via run_audit (prova de que o drift é pego) ---------------


def _write_min_agent(root: Path) -> None:
    root.joinpath("AGENTS.md").write_text(
        "---\nschema_version: 1\nproject: x\nconstraints: []\n"
        "references: {}\nbudgets: {}\n---\n",
        encoding="utf-8",
    )


def _write_min_state(state: Path) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        "---\nschema_version: 2\nupdated_at: 2026-05-04T00:00:00Z\n"
        "active_features: []\n---\n",
        encoding="utf-8",
    )


def _write_feature(features_dir: Path, fid: str, status: str, version: str) -> None:
    features_dir.mkdir(parents=True, exist_ok=True)
    features_dir.joinpath(f"{fid}-x.md").write_text(
        f"---\nid: {fid}\nname: x\nstatus: {status}\n"
        f"introduced: 2026-05-04\nversion: {version}\n"
        f"user_value: x\ncontracts: {{}}\n"
        f"acceptance:\n  - {{id: A1, pattern: ubiquitous, requirement: x}}\n"
        f"depends_on: []\ndecisions: []\n---\n",
        encoding="utf-8",
    )


def test_run_audit_flags_shipped_but_in_progress(audit_with_tmp_root):
    """Regressão controlada: o drift original (in_progress já-released)
    agora aparece como warning no relatório."""
    root = audit_with_tmp_root
    _write_min_agent(root)
    _write_min_state(root / ".feat-memory" / "STATE.md")
    _write_feature(root / ".feat-memory" / "manifest" / "features",
                   "F-0010", "in_progress", "0.6.0")
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [0.6.0] - 2026-05-04\n", encoding="utf-8",
    )

    result = audit.run_audit(write_indices=False)
    warns = [i for i in result["issues"]
             if i["severity"] == "warning" and "F-0010" in i["message"]]
    assert len(warns) == 1
