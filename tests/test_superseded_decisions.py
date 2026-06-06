"""Testes da separação de ADRs superseded (F-0019, ADR-0023)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from feat_memory.governance import audit
from feat_memory.memory import indexing, propose_adr
from feat_memory.shared import paths as _paths


@pytest.fixture
def tmp_repo(tmp_project, monkeypatch):
    am = tmp_project / ".feat-memory"
    monkeypatch.setattr(_paths, "ROOT", tmp_project, raising=False)
    monkeypatch.setattr(_paths, "AGENT", tmp_project / "AGENTS.md", raising=False)
    monkeypatch.setattr(_paths, "CLAUDE", tmp_project / "CLAUDE.md", raising=False)
    monkeypatch.setattr(_paths, "STATE", am / "STATE.md", raising=False)
    monkeypatch.setattr(_paths, "MANIFEST_DIR", am / "manifest", raising=False)
    monkeypatch.setattr(_paths, "FEATURES_DIR", am / "manifest" / "features", raising=False)
    monkeypatch.setattr(_paths, "ARCHIVE_DIR", am / "manifest" / "archive", raising=False)
    monkeypatch.setattr(_paths, "DECISIONS_DIR", am / "decisions", raising=False)
    monkeypatch.setattr(_paths, "SUPERSEDED_DIR", am / "decisions" / "superseded", raising=False)
    monkeypatch.setattr(_paths, "PROPOSALS_DIR", am / "decisions" / "proposals", raising=False)
    return tmp_project


def _write_decision(d: Path, num: str, slug: str, *, status: str = "accepted") -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{num}-{slug}.md"
    p.write_text(
        f"---\nid: ADR-{num}\ndate: 2026-01-01\nstatus: {status}\n---\n# ADR-{num}\n",
        encoding="utf-8",
    )
    return p


def _write_minimal_state(state: Path, *, active_decisions: list[str]) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---", "schema_version: 2",
        "updated_at: 2026-05-11T00:00:00Z",
        "active_features: []",
        "active_decisions:",
    ]
    lines += [f"- {a}" for a in active_decisions]
    lines += ["---", ""]
    state.write_text("\n".join(lines), encoding="utf-8")


def _write_minimal_agent(root: Path) -> None:
    (root / "AGENTS.md").write_text(
        "---\nschema_version: 1\nproject: x\nconstraints: []\n"
        "references: {}\nbudgets: {}\n---\n",
        encoding="utf-8",
    )


def test_resolve_active_decision_paths_finds_in_superseded(tmp_repo):
    _write_decision(_paths.SUPERSEDED_DIR, "0005", "old", status="superseded")
    state_fm = {"active_decisions": ["ADR-0005"]}
    paths = audit._resolve_active_decision_paths(state_fm)
    assert len(paths) == 1
    assert paths[0].name == "0005-old.md"


def test_resolve_active_decision_paths_searches_both_dirs(tmp_repo):
    _write_decision(_paths.DECISIONS_DIR, "0001", "live")
    _write_decision(_paths.SUPERSEDED_DIR, "0005", "old", status="superseded")
    state_fm = {"active_decisions": ["ADR-0001", "ADR-0005"]}
    paths = audit._resolve_active_decision_paths(state_fm)
    names = sorted(p.name for p in paths)
    assert names == ["0001-live.md", "0005-old.md"]


def test_crosscheck_resolves_superseded_via_merged_list(tmp_repo):
    """A2: crosscheck recebe lista mergeada (decisions + superseded);
    ID superseded em active_decisions não dispara erro."""
    state_fm = {"active_features": [], "active_decisions": ["ADR-0005"]}
    decisions = [{"id": "ADR-0005"}]  # mergeada na chamada de run_audit
    issues = audit.validate_state_crosscheck(state_fm, [], decisions)
    assert issues == []


def test_next_adr_number_includes_superseded(tmp_repo):
    _write_decision(_paths.DECISIONS_DIR, "0001", "live")
    _write_decision(_paths.SUPERSEDED_DIR, "0005", "old", status="superseded")
    # Reinit module-level globals em propose_adr para apontar para tmp_repo.
    propose_adr.DECISIONS_DIR = _paths.DECISIONS_DIR
    propose_adr.PROPOSALS_DIR = _paths.PROPOSALS_DIR
    assert propose_adr.next_adr_number() == 6


def test_gen_superseded_index_emits_table(tmp_repo):
    out = indexing.gen_superseded_decisions_index([
        {"id": "ADR-0005", "date": "2026-04-28", "status": "superseded",
         "tags": ["installation"], "affects_features": []},
    ])
    assert "ADR-0005" in out
    assert "superseded" in out
    assert "Índice de decisões superseded" in out


def test_regenerate_all_indexes_writes_superseded_when_present(tmp_repo):
    _write_decision(_paths.DECISIONS_DIR, "0001", "live")
    _write_decision(_paths.SUPERSEDED_DIR, "0005", "old", status="superseded")
    indexing.regenerate_all_indexes(
        _paths.MANIFEST_DIR, _paths.ARCHIVE_DIR,
        _paths.DECISIONS_DIR, _paths.SUPERSEDED_DIR,
        features=[], archived_features=[],
        decisions=[{"id": "ADR-0001", "date": "2026-01-01",
                    "status": "accepted", "tags": [], "affects_features": []}],
        superseded_decisions=[{"id": "ADR-0005", "date": "2026-04-28",
                               "status": "superseded", "tags": [],
                               "affects_features": []}],
    )
    main_idx = (_paths.DECISIONS_DIR / "INDEX.md").read_text(encoding="utf-8")
    sup_idx = (_paths.SUPERSEDED_DIR / "INDEX.md").read_text(encoding="utf-8")
    assert "ADR-0001" in main_idx
    assert "ADR-0005" not in main_idx
    assert "ADR-0005" in sup_idx
    assert "ADR-0001" not in sup_idx


def test_regenerate_skips_superseded_index_when_empty(tmp_repo):
    _write_decision(_paths.DECISIONS_DIR, "0001", "live")
    indexing.regenerate_all_indexes(
        _paths.MANIFEST_DIR, _paths.ARCHIVE_DIR,
        _paths.DECISIONS_DIR, _paths.SUPERSEDED_DIR,
        features=[], archived_features=[],
        decisions=[{"id": "ADR-0001", "date": "2026-01-01",
                    "status": "accepted", "tags": [], "affects_features": []}],
        superseded_decisions=[],
    )
    assert not (_paths.SUPERSEDED_DIR / "INDEX.md").exists()


def test_run_audit_finds_superseded_active_via_state(tmp_repo):
    _write_minimal_agent(tmp_repo)
    _write_decision(_paths.DECISIONS_DIR, "0001", "live")
    _write_decision(_paths.SUPERSEDED_DIR, "0005", "old", status="superseded")
    _write_minimal_state(_paths.STATE,
                         active_decisions=["ADR-0001", "ADR-0005"])

    args = argparse.Namespace(
        cmd="audit", json=False, no_index=False, strict=False,
        check_collisions=None, check_staleness=None, func=audit.run,
    )
    result = audit.run_audit(write_indices=True)
    crosscheck_errors = [i for i in result["issues"]
                         if i["severity"] == "error"
                         and "ADR-0005" in i.get("message", "")]
    assert crosscheck_errors == []
    assert (_paths.SUPERSEDED_DIR / "INDEX.md").exists()
