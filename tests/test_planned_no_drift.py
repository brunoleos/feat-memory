"""Audit isenta features `planned` do drift de contracts (ADR-0044).

A doutrina ADR-0041 ancora features `planned` antes do código; seus
contracts apontam para alvos que ainda não existem. Isso não é drift —
só features construídas (in_progress/shipped) sofrem o check de existência.
"""

from __future__ import annotations

import textwrap

import pytest

from feat_memory.memory import schemas
from feat_memory.shared import paths as _paths


def _write_feature(tmp_path, status: str):
    content = textwrap.dedent(f"""\
        ---
        id: F-0099
        name: alguma-capacidade
        status: {status}
        user_value: Uma capacidade qualquer.
        contracts:
          api: src/feat_memory/inexistente.py::func
          tests: tests/test_inexistente.py
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


def test_proposed_feature_skips_contract_drift(tmp_path):
    p = _write_feature(tmp_path, "proposed")
    _, issues = schemas.validate_feature(p)
    assert not any("caminho inexistente" in i.message for i in issues), issues


@pytest.mark.parametrize("status", ["in_progress", "shipped"])
def test_built_feature_still_flags_contract_drift(tmp_path, status):
    p = _write_feature(tmp_path, status)
    _, issues = schemas.validate_feature(p)
    drift = [i for i in issues if "caminho inexistente" in i.message]
    assert len(drift) == 2, issues  # api + tests
