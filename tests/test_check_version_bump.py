"""Testes do `agent-memory check-version-bump-staged` (F-0016, ADR-0020)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pytest

from agent_memory import audit, check_version_bump


# --- helpers -------------------------------------------------------------


def _stage(repo: Path, files: dict[str, str]) -> None:
    for relpath, content in files.items():
        full = repo / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", relpath], cwd=repo, check=True)


# --- needs_bump core ----------------------------------------------------


def test_needs_bump_blocks_when_code_staged_without_version(tmp_project):
    """A1: código sem VERSION → bloqueia."""
    (tmp_project / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    subprocess.run(["git", "add", "VERSION"], cwd=tmp_project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"],
                   cwd=tmp_project, check=True)
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})

    assert check_version_bump.needs_bump(tmp_project) is True


def test_needs_bump_passes_when_version_in_staging(tmp_project):
    """A2: VERSION no staging junto com código → passa."""
    (tmp_project / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    subprocess.run(["git", "add", "VERSION"], cwd=tmp_project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"],
                   cwd=tmp_project, check=True)
    _stage(tmp_project, {
        "src/foo.py": "x = 1\n",
        "VERSION": "0.2.0\n",
    })

    assert check_version_bump.needs_bump(tmp_project) is False


def test_needs_bump_passes_when_only_noncode_staged(tmp_project):
    """A3: só docs/tests no staging → não precisa bumpar."""
    (tmp_project / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    subprocess.run(["git", "add", "VERSION"], cwd=tmp_project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"],
                   cwd=tmp_project, check=True)
    _stage(tmp_project, {
        "README.md": "# hi\n",
        "tests/test_foo.py": "def test(): pass\n",
        "docs/guide.md": "# guide\n",
        ".agent-memory/manifest/features/F-0099-foo.md": "---\nid: F-0099\n---\n",
    })

    assert check_version_bump.needs_bump(tmp_project) is False


def test_needs_bump_noop_without_version_file(tmp_project):
    """A4: sem arquivo VERSION → no-op (auto opt-in)."""
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})

    assert check_version_bump.needs_bump(tmp_project) is False


def test_needs_bump_silent_on_git_failure(tmp_path):
    """A6: fail-soft sem git → sem bloqueio."""
    (tmp_path / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    # tmp_path não tem .git → git diff --cached falha
    assert check_version_bump.needs_bump(tmp_path) is False


def test_needs_bump_passes_when_nothing_staged(tmp_project):
    """staging vazio → nada para bumpar."""
    (tmp_project / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    subprocess.run(["git", "add", "VERSION"], cwd=tmp_project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"],
                   cwd=tmp_project, check=True)

    assert check_version_bump.needs_bump(tmp_project) is False


# --- run() exit code and stderr surface --------------------------------


def test_run_exits_one_when_bump_needed(tmp_project, capsys, monkeypatch):
    """A1: exit 1 + mensagem na stderr."""
    (tmp_project / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    subprocess.run(["git", "add", "VERSION"], cwd=tmp_project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"],
                   cwd=tmp_project, check=True)

    monkeypatch.setattr(audit, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})

    rc = check_version_bump.run(argparse.Namespace())

    assert rc == 1
    err = capsys.readouterr().err
    assert "VERSION" in err
    assert "SemVer" in err
    assert "--no-verify" in err


def test_run_exits_zero_silent_when_clean(tmp_project, capsys, monkeypatch):
    """A2/A3: exit 0 sem stderr quando passa."""
    (tmp_project / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    subprocess.run(["git", "add", "VERSION"], cwd=tmp_project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"],
                   cwd=tmp_project, check=True)
    monkeypatch.setattr(audit, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)
    _stage(tmp_project, {
        "src/foo.py": "x = 1\n",
        "VERSION": "0.2.0\n",
    })

    rc = check_version_bump.run(argparse.Namespace())

    assert rc == 0
    err = capsys.readouterr().err
    assert err == ""


def test_run_exits_zero_when_no_version_file(tmp_project, capsys, monkeypatch):
    """A4: sem VERSION na raiz, é no-op silencioso."""
    monkeypatch.setattr(audit, "ROOT", None, raising=False)
    monkeypatch.chdir(tmp_project)
    _stage(tmp_project, {"src/foo.py": "x = 1\n"})

    rc = check_version_bump.run(argparse.Namespace())

    assert rc == 0
    err = capsys.readouterr().err
    assert err == ""


# --- CLI surface --------------------------------------------------------


def test_subcommand_registered(capsys):
    from agent_memory import cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "check-version-bump-staged" in out
