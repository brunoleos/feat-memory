"""Smoke tests da superfície de CLI: subcomandos existem e --help responde."""

import pytest

from feat_memory import cli


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


def test_schema_subcommand_listed_and_help(capsys):
    """`schema` aparece no help top-level e responde a --help (W1)."""
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert "schema" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        cli.main(["schema", "--help"])
    assert exc.value.code == 0


def test_schema_subcommand_prints_reference(capsys):
    """`feat-memory schema` imprime a referência de schema (W1)."""
    rc = cli.main(["schema"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Referência de schema" in out
    assert "patterns EARS" in out


def test_path_positional_accepted_by_audit_migrate(capsys):
    """audit e migrate aceitam `[path]` opcional no help (W3, ADR-0033)."""
    for sub in ("audit", "migrate"):
        with pytest.raises(SystemExit) as exc:
            cli.main([sub, "--help"])
        assert exc.value.code == 0
        assert "path" in capsys.readouterr().out


def test_deploy_target_is_optional(capsys):
    """deploy aceita target opcional (default cwd) — não erra ao parsear (W3)."""
    with pytest.raises(SystemExit) as exc:
        cli.main(["deploy", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    # uso mostra target entre colchetes (opcional)
    assert "[target]" in out


def test_no_subcommand_errors():
    """Sem subcomando, argparse deve sair com código != 0 (required=True)."""
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code != 0


def test_version_flag_prints_and_exits(capsys):
    """`feat-memory --version` imprime versão e sai com 0 sem subcomando."""
    from feat_memory import __version__
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert f"feat-memory {__version__}" in out
