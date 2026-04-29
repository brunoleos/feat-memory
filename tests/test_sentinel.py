"""Testes da função _replace_sentinel_block — base da idempotência do deploy."""

from agent_memory.deploy import (
    SENTINEL_BEGIN,
    SENTINEL_END,
    _replace_sentinel_block,
)


def test_insert_into_empty():
    new, changed = _replace_sentinel_block("", "payload\n")
    assert changed is True
    assert SENTINEL_BEGIN in new
    assert "payload" in new
    assert SENTINEL_END in new


def test_insert_preserving_existing_content():
    existing = "# linha pre-existente\n"
    new, changed = _replace_sentinel_block(existing, "bloco\n")
    assert changed is True
    assert "# linha pre-existente" in new
    assert "bloco" in new
    assert new.startswith("# linha pre-existente")


def test_replaces_existing_block():
    existing = (
        "head\n"
        f"{SENTINEL_BEGIN}\n"
        "payload-antigo\n"
        f"{SENTINEL_END}\n"
        "tail\n"
    )
    new, changed = _replace_sentinel_block(existing, "payload-novo\n")
    assert changed is True
    assert "payload-antigo" not in new
    assert "payload-novo" in new
    assert "head" in new
    assert "tail" in new
    # Sentinelas não duplicadas
    assert new.count(SENTINEL_BEGIN) == 1
    assert new.count(SENTINEL_END) == 1


def test_idempotent_when_unchanged():
    first, _ = _replace_sentinel_block("", "payload\n")
    second, changed = _replace_sentinel_block(first, "payload\n")
    assert changed is False
    assert second == first


def test_appends_when_existing_has_no_block():
    existing = "linha A\nlinha B\n"
    new, changed = _replace_sentinel_block(existing, "novo\n")
    assert changed is True
    assert new.startswith("linha A\nlinha B\n")
    assert SENTINEL_BEGIN in new[len("linha A\nlinha B\n"):]
