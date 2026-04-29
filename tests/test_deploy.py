"""Testes end-to-end do `agent-memory deploy <target>`."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pytest

from agent_memory import deploy


def _args(target: Path | str, *, force: bool = False, no_merge: bool = False,
          no_hooks: bool = True) -> argparse.Namespace:
    return argparse.Namespace(
        target=str(target),
        force=force,
        no_merge=no_merge,
        no_hooks=no_hooks,
        cmd="deploy",
        func=deploy.run,
    )


def test_deploy_creates_all_artifacts(tmp_project):
    rc = deploy.run(_args(tmp_project))
    assert rc == 0

    for path in (
        tmp_project / "AGENT.md",
        tmp_project / "CLAUDE.md",
        tmp_project / "STATE.md",
        tmp_project / ".gitattributes",
        tmp_project / ".gitignore",
    ):
        assert path.is_file(), f"esperado: {path}"

    assert (tmp_project / "manifest" / "features").is_dir()
    assert (tmp_project / "decisions" / "proposals").is_dir()
    assert (tmp_project / "skills" / "memory-deploy" / "SKILL.md").is_file()
    assert (tmp_project / "skills" / "memory-bootstrap" / "SKILL.md").is_file()
    assert (tmp_project / "skills" / "memory-debrief" / "SKILL.md").is_file()


def test_deploy_is_idempotent(tmp_project):
    deploy.run(_args(tmp_project))
    rc = deploy.run(_args(tmp_project))
    assert rc == 0

    gitignore = (tmp_project / ".gitignore").read_text(encoding="utf-8")
    # Bloco de sentinelas não pode duplicar em re-execuções
    assert gitignore.count("# >>> agent-memory >>>") == 1
    assert gitignore.count("# <<< agent-memory <<<") == 1
    assert ".agent-memory-deploy/" in gitignore


def test_deploy_preserves_existing_agent_md(tmp_project):
    custom = "# Constituição custom do meu projeto\n"
    (tmp_project / "AGENT.md").write_text(custom, encoding="utf-8")

    rc = deploy.run(_args(tmp_project))
    assert rc == 0

    # Conteúdo customizado preservado
    assert (tmp_project / "AGENT.md").read_text(encoding="utf-8") == custom

    # Template novo na fila de merge
    queue = tmp_project / ".agent-memory-deploy" / "merge-queue"
    pending = tmp_project / ".agent-memory-deploy" / "pending" / "AGENT.md.new"
    assert queue.is_file()
    assert "AGENT.md" in queue.read_text(encoding="utf-8")
    assert pending.is_file()


def test_deploy_force_overwrites_existing(tmp_project):
    custom = "# meu custom\n"
    (tmp_project / "AGENT.md").write_text(custom, encoding="utf-8")

    rc = deploy.run(_args(tmp_project, force=True))
    assert rc == 0

    new_content = (tmp_project / "AGENT.md").read_text(encoding="utf-8")
    assert new_content != custom
    assert "Constituição" in new_content  # vem do template


def test_deploy_no_merge_skips_existing_without_queueing(tmp_project):
    custom = "# meu custom\n"
    (tmp_project / "AGENT.md").write_text(custom, encoding="utf-8")

    rc = deploy.run(_args(tmp_project, no_merge=True))
    assert rc == 0

    # Conteúdo preservado
    assert (tmp_project / "AGENT.md").read_text(encoding="utf-8") == custom
    # Sem fila de merge gerada
    assert not (tmp_project / ".agent-memory-deploy" / "merge-queue").exists()


def test_deploy_invalid_target_returns_error(tmp_path):
    rc = deploy.run(_args(tmp_path / "nao-existe"))
    assert rc == 1


def test_deploy_target_must_be_directory(tmp_path):
    file_path = tmp_path / "arquivo.txt"
    file_path.write_text("conteudo")
    rc = deploy.run(_args(file_path))
    assert rc == 1


def test_deploy_reaches_audit_step(tmp_project, capsys):
    """Mesmo sem o binário no PATH, o header da auditoria deve aparecer."""
    deploy.run(_args(tmp_project))
    out = capsys.readouterr().out
    assert "Auditoria inicial:" in out


@pytest.mark.skipif(
    shutil.which("agent-memory") is None,
    reason="agent-memory binary not on PATH; audit subprocess não pode rodar",
)
def test_deploy_audit_subprocess_succeeds(tmp_project, capsys):
    """Quando o binário está no PATH, a auditoria deve rodar sem warnings."""
    deploy.run(_args(tmp_project))
    out = capsys.readouterr().out
    assert "AVISO: 'agent-memory' não encontrado" not in out
    assert "auditoria retornou" not in out  # só aparece se rc != 0


def test_deploy_substitutes_version_in_agent_md(tmp_project):
    """O placeholder {VERSION} deve ser substituído pela versão atual."""
    from agent_memory import __version__
    deploy.run(_args(tmp_project))
    content = (tmp_project / "AGENT.md").read_text(encoding="utf-8")
    assert "{VERSION}" not in content
    assert f"v{__version__}/METHODOLOGY.md" in content


def test_deploy_cleans_stale_pending_dir(tmp_project):
    """Re-deploy obliterates leftover .agent-memory-deploy/ from prior run."""
    # Simula deploy anterior com merges pendentes
    deploy_dir = tmp_project / ".agent-memory-deploy"
    deploy_dir.mkdir()
    (deploy_dir / "merge-queue").write_text("STALE.md\n")
    (deploy_dir / "pending").mkdir()
    (deploy_dir / "pending" / "STALE.md.new").write_text("conteudo antigo")

    # Run deploy sem AGENT.md customizado (não dispara nova fila)
    deploy.run(_args(tmp_project))

    # Diretório de deploy não deve ter sobrado nada do estado anterior
    assert not (deploy_dir / "merge-queue").exists()
    assert not (deploy_dir / "pending" / "STALE.md.new").exists()
