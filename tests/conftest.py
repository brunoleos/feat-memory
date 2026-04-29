"""Fixtures compartilhadas pelos testes."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Cria um diretório temporário inicializado como repositório Git.

    Suficiente para testar deploy e auditoria. O usuário/email são
    configurados localmente para que `git commit` funcione se o teste
    precisar.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, check=True,
    )
    return tmp_path
