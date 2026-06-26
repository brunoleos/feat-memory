"""Conteúdo metodológico crítico das skills empacotadas (F-0039, ADR-0046).

Garante que a memory-debrief carrega o ritual de retrospectiva + captura de
sugestões e registra no UNRELEASED, e que a bootstrap lê o layout novo.
Pega regressão: uma skill voltar a citar o layout legado quebra o consumidor.
"""

from __future__ import annotations

from importlib.resources import files


def _skill(name: str) -> str:
    return (files("feat_memory") / "data" / "skills" / name / "SKILL.md").read_text(
        encoding="utf-8"
    )


def test_debrief_has_retrospective_and_ideas_triage():
    text = _skill("memory-debrief")
    assert "Retrospectiva" in text
    assert "ideas.md" in text


def test_debrief_registers_in_unreleased():
    assert "UNRELEASED" in _skill("memory-debrief")


def test_bootstrap_reads_unreleased_and_ideas_fallback():
    text = _skill("memory-bootstrap")
    assert "UNRELEASED" in text
    assert "ideas.md" in text
