"""Testes end-to-end do `agent-memory deploy <target>`."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pytest

from agent_memory import deploy
from agent_memory.shared.parsing import parse_frontmatter


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
        tmp_project / "AGENTS.md",
        tmp_project / "CLAUDE.md",
        tmp_project / ".agent-memory" / "STATE.md",
        tmp_project / ".gitattributes",
        tmp_project / ".gitignore",
    ):
        assert path.is_file(), f"esperado: {path}"

    assert (tmp_project / ".agent-memory" / "manifest" / "features").is_dir()
    assert (tmp_project / ".agent-memory" / "decisions" / "proposals").is_dir()
    assert (tmp_project / "skills" / "memory-deploy" / "SKILL.md").is_file()
    assert (tmp_project / "skills" / "memory-bootstrap" / "SKILL.md").is_file()
    assert (tmp_project / "skills" / "memory-debrief" / "SKILL.md").is_file()
    assert (tmp_project / "skills" / "memory-pull-brief" / "SKILL.md").is_file()


def test_deploy_is_idempotent(tmp_project):
    deploy.run(_args(tmp_project))
    rc = deploy.run(_args(tmp_project))
    assert rc == 0

    gitignore = (tmp_project / ".gitignore").read_text(encoding="utf-8")
    # Bloco de sentinelas não pode duplicar em re-execuções
    assert gitignore.count("# >>> agent-memory >>>") == 1
    assert gitignore.count("# <<< agent-memory <<<") == 1
    assert ".agent-memory-deploy/" in gitignore


def test_deploy_appends_methodology_block_to_existing_agent_md(tmp_project):
    """AGENTS.md já existente recebe o bloco com sentinelas anexado."""
    custom = "# Constituição custom do meu projeto\n\n## Identidade\n\nFoo.\n"
    (tmp_project / "AGENTS.md").write_text(custom, encoding="utf-8")

    rc = deploy.run(_args(tmp_project))
    assert rc == 0

    content = (tmp_project / "AGENTS.md").read_text(encoding="utf-8")
    # Conteúdo original preservado
    assert "# Constituição custom do meu projeto" in content
    assert "## Identidade" in content
    assert "Foo." in content
    # Bloco com sentinelas anexado
    assert "<!-- >>> agent-memory >>> -->" in content
    assert "<!-- <<< agent-memory <<< -->" in content
    assert "## agent-memory" in content
    # Sem fila de merge gerada (mecanismo legado removido)
    assert not (tmp_project / ".agent-memory-deploy").exists()


def test_deploy_redeploy_is_idempotent_on_block(tmp_project):
    """Re-deploy refresca o bloco sem duplicar e sem tocar conteúdo do usuário."""
    deploy.run(_args(tmp_project))
    # Usuário adiciona seção própria fora do bloco
    extra = "\n## Identidade\n\nProjeto teste.\n"
    agent_md = tmp_project / "AGENTS.md"
    agent_md.write_text(
        agent_md.read_text(encoding="utf-8") + extra, encoding="utf-8"
    )

    deploy.run(_args(tmp_project))

    final = agent_md.read_text(encoding="utf-8")
    # Seção do usuário preservada
    assert "## Identidade" in final
    assert "Projeto teste." in final
    # Bloco aparece exatamente uma vez (não duplica)
    assert final.count("<!-- >>> agent-memory >>> -->") == 1
    assert final.count("<!-- <<< agent-memory <<< -->") == 1


def test_deploy_force_overwrites_existing(tmp_project):
    custom = "# meu custom\n"
    (tmp_project / "AGENTS.md").write_text(custom, encoding="utf-8")

    rc = deploy.run(_args(tmp_project, force=True))
    assert rc == 0

    new_content = (tmp_project / "AGENTS.md").read_text(encoding="utf-8")
    assert new_content != custom
    assert "Constituição" in new_content  # vem do template


def test_deploy_no_merge_skips_existing_without_queueing(tmp_project):
    custom = "# meu custom\n"
    (tmp_project / "AGENTS.md").write_text(custom, encoding="utf-8")

    rc = deploy.run(_args(tmp_project, no_merge=True))
    assert rc == 0

    # Conteúdo preservado
    assert (tmp_project / "AGENTS.md").read_text(encoding="utf-8") == custom
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
    content = (tmp_project / "AGENTS.md").read_text(encoding="utf-8")
    assert "{VERSION}" not in content
    assert f"v{__version__}/METHODOLOGY.md" in content


def test_deploy_state_gets_real_timestamp_not_hardcoded(tmp_project):
    """STATE.md nasce com updated_at do deploy, não a data fixa do template.

    Regressão: o template tinha `updated_at: 2026-04-28` hardcoded, então a
    auditoria pós-deploy lia semanas de drift num arquivo recém-criado.
    """
    from datetime import datetime, timezone

    deploy.run(_args(tmp_project))
    fm, _ = parse_frontmatter(tmp_project / ".agent-memory" / "STATE.md")

    assert fm["updated_by"] == "deploy"
    assert "{DEPLOY_DATE}" != str(fm["updated_at"])
    ts = datetime.fromisoformat(str(fm["updated_at"]).replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    # Deploy acabou de rodar: o timestamp é recente, não 2026-04.
    assert abs((datetime.now(timezone.utc) - ts).total_seconds()) < 300


def test_deploy_injects_frontmatter_into_legacy_agent_md(tmp_project):
    """AGENTS.md em prosa, sem frontmatter, recebe o esqueleto injetado.

    Regressão (ADR-0029): antes, deploy só anexava o bloco com sentinelas e
    deixava o arquivo sem schema_version/project/..., fazendo a auditoria
    falhar com conformidade 0.00 logo após adoção legacy.
    """
    prose = "# Constituição do projeto\n\nSomos uma SPA vanilla JS.\n"
    (tmp_project / "AGENTS.md").write_text(prose, encoding="utf-8")

    rc = deploy.run(_args(tmp_project))
    assert rc == 0

    content = (tmp_project / "AGENTS.md").read_text(encoding="utf-8")
    # Frontmatter foi prependido (arquivo começa com ---)
    assert content.startswith("---\n")
    fm, _ = parse_frontmatter(tmp_project / "AGENTS.md")
    for field in ("schema_version", "project", "constraints", "references",
                  "budgets"):
        assert field in fm, f"campo obrigatório ausente após injeção: {field}"
    # Prosa do mantenedor preservada, abaixo do frontmatter
    assert "Somos uma SPA vanilla JS." in content
    # Bloco da metodologia também presente
    assert "<!-- >>> agent-memory >>> -->" in content


def test_deploy_does_not_inject_frontmatter_when_present(tmp_project):
    """AGENTS.md que já tem frontmatter não recebe um segundo bloco."""
    existing = (
        "---\nschema_version: 2\nproject: meu-proj\nconstraints: []\n"
        "references: {}\nbudgets: {}\n---\n\n# Const\n\nProsa.\n"
    )
    (tmp_project / "AGENTS.md").write_text(existing, encoding="utf-8")

    deploy.run(_args(tmp_project))

    content = (tmp_project / "AGENTS.md").read_text(encoding="utf-8")
    # Exatamente um frontmatter (uma abertura `---` no topo + um fechamento)
    assert content.startswith("---\n")
    assert content.count("\n---\n") == 1
    assert "project: meu-proj" in content
    assert "TODO-nome-do-projeto" not in content


def test_deploy_frontmatter_injection_is_idempotent(tmp_project):
    """Re-deploy não injeta um segundo esqueleto de frontmatter."""
    prose = "# Const\n\nProsa do projeto.\n"
    (tmp_project / "AGENTS.md").write_text(prose, encoding="utf-8")

    deploy.run(_args(tmp_project))
    deploy.run(_args(tmp_project))

    content = (tmp_project / "AGENTS.md").read_text(encoding="utf-8")
    assert content.count("schema_version:") == 1
    assert content.count("<!-- >>> agent-memory >>> -->") == 1


def test_deploy_defaults_to_cwd(tmp_project, monkeypatch):
    """deploy sem target usa o diretório atual (W3, ADR-0033)."""
    monkeypatch.chdir(tmp_project)
    rc = deploy.run(_args("."))
    assert rc == 0
    assert (tmp_project / "AGENTS.md").is_file()
    assert (tmp_project / ".agent-memory" / "STATE.md").is_file()


def test_deploy_meta_omits_cli_path(tmp_project):
    """meta.yaml não versiona mais cli_path (W6, ADR-0034)."""
    import yaml
    deploy.run(_args(tmp_project))
    data = yaml.safe_load(
        (tmp_project / ".agent-memory" / ".meta.yaml").read_text(encoding="utf-8")
    )
    assert "cli_path" not in data
    assert data["version"]


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
