"""Testes do campo `version` opcional em ADRs (F-0023, ADR-0027)."""

from __future__ import annotations

from pathlib import Path

from agent_memory.memory import schemas, propose_adr


def _write_decision(d: Path, body_fm: str) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / "0099-exemplo.md"
    p.write_text(f"---\n{body_fm}---\n\n# ADR-0099\n", encoding="utf-8")
    return p


BASE = "id: ADR-0099\ndate: 2026-06-03\nstatus: accepted\n"


def test_version_valido_nao_emite_issue(tmp_path: Path):
    p = _write_decision(tmp_path, BASE + "version: 0.11.0\n")
    _, issues = schemas.validate_decision(p)
    assert [i for i in issues if "version" in i.message] == []


def test_version_ausente_e_valido(tmp_path: Path):
    """ADR sem version permanece válido — campo nunca é exigido (ADR-0003)."""
    p = _write_decision(tmp_path, BASE)
    _, issues = schemas.validate_decision(p)
    assert [i for i in issues if "version" in i.message] == []


def test_version_malformado_emite_error(tmp_path: Path):
    p = _write_decision(tmp_path, BASE + "version: '0.11'\n")
    _, issues = schemas.validate_decision(p)
    errs = [i for i in issues if "version" in i.message and i.severity == "error"]
    assert len(errs) == 1


def test_version_com_v_prefix_e_valido(tmp_path: Path):
    """Prefixo `v` é aceito por compat com ADRs da gênese (vX.Y.Z)."""
    p = _write_decision(tmp_path, BASE + "version: v1.0.0\n")
    _, issues = schemas.validate_decision(p)
    assert [i for i in issues if "version" in i.message] == []


def test_version_texto_livre_emite_error(tmp_path: Path):
    p = _write_decision(tmp_path, BASE + "version: 'release-1'\n")
    _, issues = schemas.validate_decision(p)
    assert any("version" in i.message and i.severity == "error" for i in issues)


def test_draft_gerado_inclui_version(monkeypatch):
    """O template do propose-adr pré-preenche version com a versão do pacote."""
    monkeypatch.setattr(propose_adr, "next_adr_number", lambda: 99)
    _filename, content = propose_adr.generate_draft(
        stats={"files": 1, "insertions": 1, "deletions": 0},
        files=["x.py"], messages=["msg"], signals=[],
    )
    assert "version:" in content.split("---")[1]
