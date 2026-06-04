"""Anti-drift da referência de schema (W1).

A referência é gerada de `schemas.py`. Estes testes garantem que (a) o doc
commitado em docs/SCHEMA-REFERENCE.md está em sincronia com o gerador, e (b) o
gerador realmente cobre os enums/patterns/required de schemas.py — de modo que
o agente nunca precise ler o código-fonte para descobrir o schema.
"""

from __future__ import annotations

from pathlib import Path

from agent_memory.memory import schemas as S
from agent_memory.memory.schema_reference import render_schema_reference

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs" / "SCHEMA-REFERENCE.md"


def test_committed_doc_matches_generator():
    """docs/SCHEMA-REFERENCE.md == saída do gerador (regenere se falhar)."""
    assert DOC.is_file(), f"doc ausente: {DOC}"
    expected = render_schema_reference()
    actual = DOC.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/SCHEMA-REFERENCE.md divergiu de schemas.py. Regere com:\n"
        "  agent-memory schema > docs/SCHEMA-REFERENCE.md"
    )


def test_reference_covers_all_ears_patterns():
    ref = render_schema_reference()
    for pattern in S.EARS_PATTERN_FIELDS:
        assert f"`{pattern}`" in ref, f"pattern EARS ausente na referência: {pattern}"


def test_reference_covers_all_status_enums():
    ref = render_schema_reference()
    for status in S.VALID_FEATURE_STATUS | S.VALID_DECISION_STATUS:
        assert f"`{status}`" in ref, f"status ausente na referência: {status}"


def test_reference_lists_required_fields():
    ref = render_schema_reference()
    for field in (S.AGENT_REQUIRED + S.STATE_REQUIRED
                  + S.FEATURE_REQUIRED + S.DECISION_REQUIRED):
        assert f"`{field}`" in ref, f"campo obrigatório ausente na referência: {field}"


def test_dead_budget_not_referenced():
    """feature_file_max_bytes foi removido (W4) — não deve reaparecer."""
    assert "feature_file_max_bytes" not in render_schema_reference()
