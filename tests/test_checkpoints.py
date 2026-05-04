"""Testes de F-0015 / ADR-0018 / ADR-0019: checkpoints append-only + STATE view."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from agent_memory import audit, checkpoints, migrate


# --- helpers -------------------------------------------------------------


def _seed_meta(root: Path, *, state_view_window: int | None = None) -> None:
    am = root / ".agent-memory"
    am.mkdir(parents=True, exist_ok=True)
    extra = (
        f"state_view_window: {state_view_window}\n"
        if state_view_window is not None else ""
    )
    (am / ".meta.yaml").write_text(
        "schema_version: 1\n"
        "version: 0.6.0\n"
        "deployed_at: 2026-05-04T00:00:00+00:00\n"
        "cli_path: /tmp/agent-memory\n"
        f"telemetry_enabled: true\n{extra}",
        encoding="utf-8",
    )


@pytest.fixture
def cp_root(tmp_path, monkeypatch):
    """Tmp project com audit.ROOT apontado e .meta.yaml semeado."""
    _seed_meta(tmp_path)
    monkeypatch.setattr(audit, "ROOT", tmp_path, raising=False)
    return tmp_path


# --- append_checkpoint ---------------------------------------------------


def test_append_creates_file_with_iso_timestamp(cp_root):
    path = checkpoints.append_checkpoint(
        cp_root,
        summary="initial",
        current="working on F-0015",
        next_="add tests",
        features=["F-0015"],
        decisions=["ADR-0018"],
        author="test",
    )
    assert path.exists()
    assert path.parent == cp_root / ".agent-memory" / "checkpoints"
    # filename é YYYY-MM-DD-HHMMSS.md
    import re
    assert re.match(r"^\d{4}-\d{2}-\d{2}-\d{6}\.md$", path.name)


def test_append_writes_required_frontmatter_fields(cp_root):
    path = checkpoints.append_checkpoint(
        cp_root,
        summary="initial",
        current="now",
        next_="later",
        features=["F-0001"],
        decisions=["ADR-0001"],
        blocked_on="external review",
        author="alice",
    )
    fm, body = audit.parse_frontmatter(path)
    assert fm["schema_version"] == 1
    assert fm["author"] == "alice"
    assert fm["current"] == "now"
    assert fm["next"] == "later"
    assert fm["summary"] == "initial"
    assert fm["active_features"] == ["F-0001"]
    assert fm["active_decisions"] == ["ADR-0001"]
    assert fm["blocked_on"] == "external review"
    assert "ts" in fm


def test_append_inherits_from_prior_when_args_omitted(cp_root):
    checkpoints.append_checkpoint(
        cp_root,
        summary="first",
        features=["F-0001"],
        decisions=["ADR-0001"],
        blocked_on="X",
        author="alice",
        next_="step-2",
    )
    p2 = checkpoints.append_checkpoint(
        cp_root,
        summary="second",
        # current/next/features/decisions/blocked_on omitidos
        author="alice",
    )
    fm, _ = audit.parse_frontmatter(p2)
    assert fm["active_features"] == ["F-0001"]
    assert fm["active_decisions"] == ["ADR-0001"]
    assert fm["blocked_on"] == "X"
    assert fm["next"] == "step-2"


def test_append_resolves_collision_with_suffix(cp_root, monkeypatch):
    """A2: dois checkpoints no mesmo segundo geram nomes diferentes."""
    fixed = datetime(2026, 5, 4, 15, 30, 42, tzinfo=timezone.utc)
    p1 = checkpoints.append_checkpoint(cp_root, summary="a", now=fixed)
    p2 = checkpoints.append_checkpoint(cp_root, summary="b", now=fixed)
    p3 = checkpoints.append_checkpoint(cp_root, summary="c", now=fixed)

    assert p1.name == "2026-05-04-153042.md"
    assert p2.name == "2026-05-04-153042-1.md"
    assert p3.name == "2026-05-04-153042-2.md"


def test_append_does_not_modify_prior_checkpoints(cp_root):
    """A2: checkpoints existentes nunca são modificados."""
    p1 = checkpoints.append_checkpoint(cp_root, summary="first", author="alice")
    content_before = p1.read_text(encoding="utf-8")
    time.sleep(0.05)
    checkpoints.append_checkpoint(cp_root, summary="second", author="bob")
    content_after = p1.read_text(encoding="utf-8")
    assert content_before == content_after


def test_append_supports_body(cp_root):
    p = checkpoints.append_checkpoint(
        cp_root,
        summary="x",
        body="reflexão livre da sessão.\nlinha 2.\n",
        author="test",
    )
    fm, body = audit.parse_frontmatter(p)
    assert "reflexão livre" in body
    assert "linha 2" in body


# --- list_checkpoints ----------------------------------------------------


def test_list_checkpoints_returns_sorted(cp_root):
    fixed1 = datetime(2026, 5, 4, 10, 0, 0, tzinfo=timezone.utc)
    fixed2 = datetime(2026, 5, 4, 11, 0, 0, tzinfo=timezone.utc)
    fixed3 = datetime(2026, 5, 4, 12, 0, 0, tzinfo=timezone.utc)
    checkpoints.append_checkpoint(cp_root, summary="b", now=fixed2)
    checkpoints.append_checkpoint(cp_root, summary="c", now=fixed3)
    checkpoints.append_checkpoint(cp_root, summary="a", now=fixed1)

    paths = checkpoints.list_checkpoints(cp_root)
    assert [p.name for p in paths] == [
        "2026-05-04-100000.md",
        "2026-05-04-110000.md",
        "2026-05-04-120000.md",
    ]


def test_list_checkpoints_handles_missing_dir(tmp_path):
    assert checkpoints.list_checkpoints(tmp_path) == []


# --- render_state --------------------------------------------------------


def test_render_state_uses_latest_checkpoint(cp_root):
    fixed1 = datetime(2026, 5, 4, 10, 0, 0, tzinfo=timezone.utc)
    fixed2 = datetime(2026, 5, 4, 11, 0, 0, tzinfo=timezone.utc)
    checkpoints.append_checkpoint(
        cp_root, summary="old", current="old current", next_="old next",
        features=["F-0001"], author="alice", now=fixed1,
    )
    checkpoints.append_checkpoint(
        cp_root, summary="new", current="new current", next_="new next",
        features=["F-0002"], author="bob", now=fixed2,
    )

    rendered = checkpoints.render_state(cp_root)
    assert "## Current" in rendered
    assert "new current" in rendered
    assert "new next" in rendered
    assert "F-0002" in rendered


def test_render_state_frontmatter_matches_legacy_schema(cp_root):
    fixed = datetime(2026, 5, 4, 10, 0, 0, tzinfo=timezone.utc)
    checkpoints.append_checkpoint(
        cp_root, summary="x", current="c", next_="n",
        features=["F-0001"], decisions=["ADR-0001"],
        blocked_on=None, author="test", now=fixed,
    )
    rendered = checkpoints.render_state(cp_root)
    # Parse o frontmatter do conteúdo gerado
    end = rendered.find("---\n", 4)
    fm = yaml.safe_load(rendered[4:end])
    assert fm["schema_version"] == 2
    assert fm["updated_by"] == "test"
    assert fm["active_features"] == ["F-0001"]
    assert fm["active_decisions"] == ["ADR-0001"]
    assert fm["blocked_on"] is None
    assert "updated_at" in fm


def test_render_state_recent_table_shows_prior_checkpoints(cp_root):
    for i in range(7):
        ts = datetime(2026, 5, 4, 10, i, 0, tzinfo=timezone.utc)
        checkpoints.append_checkpoint(
            cp_root, summary=f"sess{i}", current=f"current{i}",
            features=["F-0001"], author="test", now=ts,
        )

    rendered = checkpoints.render_state(cp_root)
    # default window=1 → últimos 5 anteriores na Recent
    assert "## Recent" in rendered
    # 7 checkpoints; latest (sess6) é o "current"; restantes 6 anteriores;
    # default recent_rows=5 → vê sess1..sess5 (sess0 fora da janela)
    assert "sess5" in rendered
    assert "sess1" in rendered
    assert "sess0" not in rendered  # fora da janela


def test_render_state_handles_no_checkpoints(cp_root):
    rendered = checkpoints.render_state(cp_root)
    assert "schema_version: 2" in rendered
    assert "## Current" in rendered
    assert "nenhum checkpoint" in rendered.lower()


def test_render_state_window_from_meta_yaml(tmp_path, monkeypatch):
    _seed_meta(tmp_path, state_view_window=2)
    monkeypatch.setattr(audit, "ROOT", tmp_path, raising=False)

    fixed1 = datetime(2026, 5, 4, 10, 0, 0, tzinfo=timezone.utc)
    fixed2 = datetime(2026, 5, 4, 11, 0, 0, tzinfo=timezone.utc)
    checkpoints.append_checkpoint(
        tmp_path, summary="a", current="alpha", next_="na",
        author="t", now=fixed1,
    )
    checkpoints.append_checkpoint(
        tmp_path, summary="b", current="beta", next_="nb",
        author="t", now=fixed2,
    )

    rendered = checkpoints.render_state(tmp_path)
    # Com window=2, ambos current devem aparecer como bullets
    assert "alpha" in rendered
    assert "beta" in rendered


# --- write_state ---------------------------------------------------------


def test_write_state_overwrites_state_md(cp_root):
    checkpoints.append_checkpoint(cp_root, summary="x", current="y",
                                  author="t")
    path = checkpoints.write_state(cp_root)
    assert path == cp_root / ".agent-memory" / "STATE.md"
    text = path.read_text(encoding="utf-8")
    assert "y" in text


# --- run_checkpoint ------------------------------------------------------


def test_run_checkpoint_appends_and_renders(cp_root, monkeypatch, capsys):
    monkeypatch.setattr(audit, "ROOT", cp_root, raising=False)
    args = argparse.Namespace(
        summary="test sess",
        current="doing it",
        next_="next thing",
        features="F-0010,F-0011",
        decisions="ADR-0014",
        blocked_on=None,
        author="claude",
        cmd="checkpoint",
    )
    rc = checkpoints.run_checkpoint(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "checkpoint gravado" in out
    assert "STATE.md regerado" in out

    cps = checkpoints.list_checkpoints(cp_root)
    assert len(cps) == 1
    fm, _ = audit.parse_frontmatter(cps[0])
    assert fm["active_features"] == ["F-0010", "F-0011"]
    assert fm["active_decisions"] == ["ADR-0014"]


def test_run_state_rebuild_without_checkpoints_errors(cp_root, monkeypatch, capsys):
    monkeypatch.setattr(audit, "ROOT", cp_root, raising=False)
    rc = checkpoints.run_state_rebuild(argparse.Namespace())
    assert rc == 1
    err = capsys.readouterr().err
    assert "Nenhum checkpoint" in err


def test_run_state_rebuild_regenerates_state(cp_root, monkeypatch, capsys):
    monkeypatch.setattr(audit, "ROOT", cp_root, raising=False)
    checkpoints.append_checkpoint(cp_root, summary="x", current="y", author="t")
    state_path = cp_root / ".agent-memory" / "STATE.md"
    # apaga STATE.md para verificar re-render
    if state_path.exists():
        state_path.unlink()
    rc = checkpoints.run_state_rebuild(argparse.Namespace())
    assert rc == 0
    assert state_path.exists()
    assert "y" in state_path.read_text(encoding="utf-8")


# --- migrate --to=checkpoints --------------------------------------------


def test_migrate_to_checkpoints_creates_initial(tmp_project, monkeypatch):
    am = tmp_project / ".agent-memory"
    am.mkdir(parents=True, exist_ok=True)
    _seed_meta(tmp_project)
    state_path = am / "STATE.md"
    state_path.write_text(
        "---\n"
        "schema_version: 2\n"
        "updated_at: 2026-04-30T17:58:00Z\n"
        "updated_by: claude-opus-4.7\n"
        "active_features: [F-0007, F-0009]\n"
        "active_decisions: [ADR-0011]\n"
        "blocked_on: null\n"
        "---\n\n"
        "## Current\n\n"
        "Implementação de F-0009 em curso.\n\n"
        "## Next\n\n"
        "Revisão e commit.\n\n"
        "## Recent\n\n"
        "| ts | agent | features | summary |\n"
        "|---|---|---|---|\n"
        "| 2026-04-30 | claude | F-0007 | foo |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(audit, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)

    args = argparse.Namespace(to="checkpoints", limit=100, json=False)
    rc = migrate.run(args)
    assert rc == 0

    cps = checkpoints.list_checkpoints(tmp_project)
    assert len(cps) == 1
    fm, body = audit.parse_frontmatter(cps[0])
    assert fm["author"] == "claude-opus-4.7"
    assert "F-0007" in fm["active_features"]
    assert "ADR-0011" in fm["active_decisions"]
    assert "Implementação de F-0009" in fm["current"]
    assert "Revisão e commit" in fm["next"]
    # corpo preservado para histórico
    assert "Recent" in body or "claude" in body


def test_migrate_to_checkpoints_is_idempotent(tmp_project, monkeypatch, capsys):
    am = tmp_project / ".agent-memory"
    cp_dir = am / "checkpoints"
    cp_dir.mkdir(parents=True, exist_ok=True)
    (cp_dir / "2026-01-01-000000.md").write_text(
        "---\nschema_version: 1\n---\n", encoding="utf-8",
    )
    _seed_meta(tmp_project)
    monkeypatch.setattr(audit, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)

    args = argparse.Namespace(to="checkpoints", limit=100, json=False)
    rc = migrate.run(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "idempotente" in out.lower() or "já existem" in out.lower()


def test_migrate_to_checkpoints_without_state_md_errors(tmp_project, monkeypatch, capsys):
    """Sem STATE.md legado: erro claro."""
    am = tmp_project / ".agent-memory"
    am.mkdir(parents=True, exist_ok=True)
    _seed_meta(tmp_project)
    monkeypatch.setattr(audit, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)

    args = argparse.Namespace(to="checkpoints", limit=100, json=False)
    rc = migrate.run(args)
    err = capsys.readouterr().err
    assert rc == 1
    assert "STATE.md" in err


# --- CLI surface --------------------------------------------------------


def test_subcommands_registered(capsys):
    from agent_memory import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "checkpoint" in out
    assert "state-rebuild" in out
