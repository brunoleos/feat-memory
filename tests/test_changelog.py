"""changelog.py — pasta por-tag + UNRELEASED vivo + retomada derivada.

Cobre ADR-0042 (histórico por-tag, INDEX gerado) e ADR-0043 (UNRELEASED +
orçamento de retomada derivado das refs).
"""

from __future__ import annotations

import argparse
import textwrap

import pytest

from feat_memory.memory import changelog
from feat_memory.shared import paths as _paths


@pytest.fixture
def root(tmp_path):
    (tmp_path / ".feat-memory").mkdir()
    (tmp_path / "VERSION").write_text("1.6.0\n", encoding="utf-8")
    return tmp_path


def _write_unreleased(root, body: str):
    changelog.ensure_scaffold(root)
    content = "---\nschema_version: 1\n---\n\n# Não-lançado\n\n" + body + "\n"
    changelog.unreleased_path(root).write_text(content, encoding="utf-8")


# --- scaffold / derive ---------------------------------------------------


def test_ensure_scaffold_idempotent(root):
    changelog.ensure_scaffold(root)
    up = changelog.unreleased_path(root)
    assert up.exists()
    up.write_text("modificado", encoding="utf-8")
    changelog.ensure_scaffold(root)  # não sobrescreve existente
    assert up.read_text(encoding="utf-8") == "modificado"


def test_derive_active_refs_from_unreleased(root):
    _write_unreleased(root, "## Adicionado\n- changelog folder (F-0035, ADR-0042)\n"
                            "- dissolve STATE (F-0036, ADR-0043)\n")
    active = changelog.derive_active_refs(root)
    assert active["features"] == ["F-0035", "F-0036"]
    assert active["decisions"] == ["ADR-0042", "ADR-0043"]


def test_derive_active_refs_empty_when_no_refs(root):
    changelog.ensure_scaffold(root)
    active = changelog.derive_active_refs(root)
    assert active == {"features": [], "decisions": []}


# --- bump validation -----------------------------------------------------


@pytest.mark.parametrize("cur,tgt,ok", [
    ("1.6.0", "1.7.0", True),
    ("1.6.0", "2.0.0", True),
    ("1.6.0", "1.6.1", True),
    ("1.6.0", "1.6.0", False),
    ("1.6.0", "1.5.0", False),
])
def test_is_forward_bump(cur, tgt, ok):
    assert changelog.is_forward_bump(cur, tgt) is ok


# --- freeze / release ----------------------------------------------------


def test_freeze_unreleased_creates_immutable_release(root):
    _write_unreleased(root, "## Adicionado\n- algo (F-0035)\n")
    target = changelog.freeze_unreleased(root, "1.7.0", "2026-06-26")
    assert target.name == "1.7.0.md"
    fm, body = changelog.parse_frontmatter(target)
    assert fm["version"] == "1.7.0" and str(fm["date"]) == "2026-06-26"
    assert "F-0035" in body
    # UNRELEASED reiniciado (sem a entrada antiga)
    assert "F-0035" not in changelog.unreleased_path(root).read_text(encoding="utf-8")
    # imutável: refreezar a mesma versão falha
    with pytest.raises(FileExistsError):
        changelog.freeze_unreleased(root, "1.7.0", "2026-06-26")


def test_index_lists_releases_newest_first(root):
    changelog.ensure_scaffold(root)
    changelog.freeze_unreleased(root, "1.7.0", "2026-06-26")
    changelog.freeze_unreleased(root, "1.8.0", "2026-06-27")
    idx = changelog.index_path(root).read_text(encoding="utf-8")
    assert idx.index("1.8.0") < idx.index("1.7.0")  # mais recente primeiro


def test_list_releases_sorted_by_semver(root):
    changelog.ensure_scaffold(root)
    for v in ["1.10.0", "1.9.0", "1.7.0"]:
        changelog.release_path(root, v).write_text(
            f"---\nversion: {v}\ndate: x\n---\n", encoding="utf-8")
    names = [p.stem for p in changelog.list_releases(root)]
    assert names == ["1.7.0", "1.9.0", "1.10.0"]  # 10 > 9, não lexical


# --- run_release (CLI) ---------------------------------------------------


@pytest.fixture
def _patch_root(root, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", root, raising=False)
    monkeypatch.setattr(_paths, "_init_paths", lambda: None)
    return root


def _args(version, date=None, allow_empty=False):
    return argparse.Namespace(version=version, date=date, allow_empty=allow_empty)


def test_run_release_happy_path(_patch_root):
    _write_unreleased(_patch_root, "## Adicionado\n- algo (F-0035, ADR-0042)\n")
    rc = changelog.run_release(_args("1.7.0", date="2026-06-26"))
    assert rc == 0
    assert changelog.release_path(_patch_root, "1.7.0").exists()
    assert changelog.read_version(_patch_root) == "1.7.0"


def test_run_release_rejects_non_forward_bump(_patch_root):
    _write_unreleased(_patch_root, "- x (F-0035)\n")
    assert changelog.run_release(_args("1.5.0")) == 1


def test_run_release_rejects_empty_without_flag(_patch_root):
    changelog.ensure_scaffold(_patch_root)  # UNRELEASED sem refs
    assert changelog.run_release(_args("1.7.0")) == 1
    assert changelog.run_release(_args("1.7.0", allow_empty=True)) == 0
