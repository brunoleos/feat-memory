"""Smoke tests do entry point real (binário no PATH).

Cobre o caminho que `tests/test_cli.py` não exercita: o setup do
`[project.scripts]` em pyproject.toml. Se o entry point estiver
quebrado mas `cli.main()` ainda funcionar, este teste pega.

Pulado quando `agent-memory` não está no PATH (típico em ambientes que
não rodaram `pip install -e ".[dev]"` no venv ativo).
"""

from __future__ import annotations

import shutil
import subprocess

import pytest


_BIN = shutil.which("agent-memory")
_skip_no_bin = pytest.mark.skipif(
    _BIN is None,
    reason="agent-memory binary not on PATH",
)


@_skip_no_bin
def test_binary_help_lists_subcommands():
    result = subprocess.run(
        [_BIN, "--help"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    for sub in ("deploy", "audit", "propose-adr", "migrate"):
        assert sub in result.stdout


@_skip_no_bin
def test_binary_no_args_errors():
    result = subprocess.run(
        [_BIN],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
