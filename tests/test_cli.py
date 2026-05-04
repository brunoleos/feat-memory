"""Smoke tests da superfície de CLI: subcomandos existem e --help responde."""

import pytest

from agent_memory import cli


def test_top_level_help_lists_all_subcommands(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for sub in ("deploy", "audit", "propose-adr", "migrate"):
        assert sub in out


def test_deploy_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["deploy", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "target" in out
    for flag in ("--force", "--no-merge", "--no-hooks"):
        assert flag in out


def test_audit_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["audit", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for flag in ("--strict", "--json", "--no-index", "--check-collisions"):
        assert flag in out


def test_propose_adr_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["propose-adr", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for flag in ("--staged", "--prompt", "--base"):
        assert flag in out


def test_migrate_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["migrate", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for flag in ("--limit", "--json"):
        assert flag in out


def test_no_subcommand_errors():
    """Sem subcomando, argparse deve sair com código != 0 (required=True)."""
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code != 0


def test_version_flag_prints_and_exits(capsys):
    """`agent-memory --version` imprime versão e sai com 0 sem subcomando."""
    from agent_memory import __version__
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert f"agent-memory {__version__}" in out
