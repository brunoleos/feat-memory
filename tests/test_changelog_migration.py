"""Migração do layout legado → changelog/ + UNRELEASED (F-0037, ADR-0042/0043)."""

from __future__ import annotations

import pytest

from feat_memory.memory import changelog


LEGACY_CHANGELOG = """\
# Changelog

Intro qualquer.

## [Unreleased]

- trabalho em voo (F-0035)

## [1.0.0] - 2026-06-06

### Adicionado
- primeira release (ADR-0036)

## [0.9.0] - 2026-05-11

- algo antigo
"""

LEGACY_STATE = """\
---
schema_version: 2
updated_at: '2026-06-25T00:00:00+00:00'
updated_by: x
active_features:
- F-0040
active_decisions:
- ADR-0099
blocked_on: null
---

# Estado

## Current

reconciliação ADR↔código do motor físico

## Next

implementar routing no motor unificado
"""


LEGACY_AGENTS = """\
---
references:
  manifest_index: ./.feat-memory/manifest/INDEX.md
  state: ./.feat-memory/STATE.md
  decisions_index: ./.feat-memory/decisions/INDEX.md
budgets:
  resumption_max_bytes: 12288
  state_max_bytes: 4096
---

# Constituição
"""


@pytest.fixture
def legacy(tmp_path):
    (tmp_path / ".feat-memory").mkdir()
    (tmp_path / "CHANGELOG.md").write_text(LEGACY_CHANGELOG, encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(LEGACY_AGENTS, encoding="utf-8")
    (tmp_path / ".feat-memory" / "STATE.md").write_text(LEGACY_STATE, encoding="utf-8")
    cp = tmp_path / ".feat-memory" / "checkpoints"
    cp.mkdir()
    (cp / "2026-01-01-000000.md").write_text("---\nx: 1\n---\n", encoding="utf-8")
    return tmp_path


def test_migrate_splits_changelog_and_removes_legacy(legacy):
    changed, msg = changelog.migrate_to_changelog_folder(legacy)
    assert changed, msg
    # releases por tag
    assert changelog.release_path(legacy, "1.0.0").exists()
    assert changelog.release_path(legacy, "0.9.0").exists()
    fm, body = changelog.parse_frontmatter(changelog.release_path(legacy, "1.0.0"))
    assert fm["version"] == "1.0.0" and str(fm["date"]) == "2026-06-06"
    assert "primeira release" in body
    # UNRELEASED com o não-lançado + seed do STATE
    up = changelog.unreleased_path(legacy).read_text(encoding="utf-8")
    assert "F-0035" in up                          # do [Unreleased]
    assert "F-0040" in up and "ADR-0099" in up     # seed do STATE (refs)
    assert "reconciliação ADR" in up               # prosa de Current preservada
    assert "implementar routing" in up             # prosa de Next preservada
    # INDEX gerado
    assert changelog.index_path(legacy).exists()
    # legados removidos
    assert not (legacy / "CHANGELOG.md").exists()
    assert not (legacy / ".feat-memory" / "STATE.md").exists()
    assert not (legacy / ".feat-memory" / "checkpoints").exists()


def test_migrate_patches_agents_frontmatter(legacy):
    """references.state→unreleased e state_max_bytes removido (#1 do dogfood)."""
    changelog.migrate_to_changelog_folder(legacy)
    text = (legacy / "AGENTS.md").read_text(encoding="utf-8")
    assert "state: ./.feat-memory/STATE.md" not in text
    assert "unreleased: ./.feat-memory/changelog/UNRELEASED.md" in text
    assert "state_max_bytes" not in text


def test_patch_frontmatter_handles_legacy_agent_memory_paths(tmp_path):
    """O patcher casa o nome de pasta legado .agent-memory/ e retorna só o que
    mudou — o defeito 2.2.1 (regex só casava .feat-memory/ + log falso-positivo)."""
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "---\nreferences:\n  manifest_index: ./.agent-memory/manifest/INDEX.md\n"
        "  state: ./.agent-memory/STATE.md\nbudgets:\n  state_max_bytes: 4096\n---\n# c\n",
        encoding="utf-8")
    changes = changelog.patch_agents_frontmatter(tmp_path)
    text = agents.read_text(encoding="utf-8")
    assert "unreleased: ./.feat-memory/changelog/UNRELEASED.md" in text
    assert ".agent-memory/" not in text     # normalizado (rename ADR-0039)
    assert "state_max_bytes" not in text
    assert len(changes) == 3                # 3 mudanças reais, não falso-positivo


def test_patch_frontmatter_no_false_positive(tmp_path):
    """Frontmatter já correto → retorna [] (sem log mentiroso)."""
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "---\nreferences:\n  unreleased: ./.feat-memory/changelog/UNRELEASED.md\n---\n# c\n",
        encoding="utf-8")
    assert changelog.patch_agents_frontmatter(tmp_path) == []


def test_migrate_is_idempotent(legacy):
    changelog.migrate_to_changelog_folder(legacy)
    changed, msg = changelog.migrate_to_changelog_folder(legacy)
    assert not changed and "já migrado" in msg


def test_migrate_derive_picks_up_seeded_refs(legacy):
    changelog.migrate_to_changelog_folder(legacy)
    active = changelog.derive_active_refs(legacy)
    assert "F-0035" in active["features"]
    assert "F-0040" in active["features"]
    assert "ADR-0099" in active["decisions"]


def test_migrate_noop_when_nothing_to_migrate(tmp_path):
    (tmp_path / ".feat-memory").mkdir()
    changed, msg = changelog.migrate_to_changelog_folder(tmp_path)
    assert not changed and "nada a migrar" in msg
