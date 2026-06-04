"""Guard de upgrade (W5): liga schema 0.00 por frontmatter ausente ao notice
de versão, imprimindo a remediação dirigida (re-rodar deploy).
"""

from __future__ import annotations

import pytest

from agent_memory import cli


def _consumer(tmp_path, *, meta_version: str) -> None:
    """Monta um consumidor mínimo: AGENTS.md SEM frontmatter + meta com versão."""
    (tmp_path / "AGENTS.md").write_text(
        "# Constituição\n\nProsa, sem frontmatter.\n", encoding="utf-8"
    )
    am = tmp_path / ".agent-memory"
    am.mkdir()
    (am / ".meta.yaml").write_text(
        f"schema_version: 1\nversion: {meta_version}\n"
        "telemetry_enabled: true\n",
        encoding="utf-8",
    )


def test_guard_fires_when_frontmatter_missing_and_cli_newer(tmp_path, capsys):
    _consumer(tmp_path, meta_version="0.0.1")  # bem mais antigo que o CLI
    cli.main(["audit", str(tmp_path), "--no-index"])
    err = capsys.readouterr().err
    assert "re-rode `agent-memory deploy`" in err
    assert "esqueleto de frontmatter" in err


def test_guard_silent_when_versions_match(tmp_path, capsys):
    from agent_memory import __version__
    _consumer(tmp_path, meta_version=__version__)  # mesma versão → sem notice
    cli.main(["audit", str(tmp_path), "--no-index"])
    err = capsys.readouterr().err
    assert "re-rode `agent-memory deploy`" not in err
