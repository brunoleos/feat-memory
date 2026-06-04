"""Guard anti-changelog no Manifest (ADR-0035).

`validate_feature` bloqueia (error) features cujo NOME é um balde de changelog
(polish, misc, various, …). Sinal de alta precisão; a coesão de conteúdo fica
para o litmus humano nas skills de autoria, não para um checker ruidoso.
"""

from __future__ import annotations

import textwrap

import pytest

from agent_memory.memory import schemas
from agent_memory.shared import paths as _paths


def _write_feature(tmp_path, name: str):
    content = textwrap.dedent(f"""\
        ---
        id: F-0099
        name: {name}
        status: shipped
        user_value: Uma capacidade qualquer.
        contracts: {{}}
        acceptance:
          - {{id: A1, pattern: ubiquitous, requirement: "invariante"}}
        ---
        corpo
        """)
    p = tmp_path / "F-0099-x.md"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _root(tmp_path, monkeypatch):
    monkeypatch.setattr(_paths, "ROOT", tmp_path, raising=False)


def test_changelog_name_is_blocked(tmp_path):
    """O nome real do F-0030 dissolvido teria sido pego."""
    p = _write_feature(tmp_path, "legacy-onboarding-polish")
    _, issues = schemas.validate_feature(p)
    errs = [i for i in issues if i.severity == "error"]
    assert any("changelog" in i.message for i in errs), errs


@pytest.mark.parametrize("name", ["misc", "various-fixes", "assorted-tweaks", "diversos"])
def test_bucket_tokens_blocked(tmp_path, name):
    p = _write_feature(tmp_path, name)
    _, issues = schemas.validate_feature(p)
    assert any("changelog" in i.message for i in issues if i.severity == "error")


@pytest.mark.parametrize("name", [
    "schema-reference", "legacy-onboarding-baseline", "cli-path-uniformity",
    "constraint-enforcement", "frontmatter-authorship",
])
def test_capability_names_pass(tmp_path, name):
    """Nenhum nome de capacidade real trip o guard (precisão alta)."""
    p = _write_feature(tmp_path, name)
    _, issues = schemas.validate_feature(p)
    assert not any("changelog" in i.message for i in issues)


def test_blocklist_is_nonempty_and_lowercase():
    assert schemas.CHANGELOG_NAME_WORDS
    assert all(w == w.lower() for w in schemas.CHANGELOG_NAME_WORDS)
