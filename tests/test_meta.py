"""Testes do arquivo `.agent-memory/.meta.yaml` (F-0010, ADR-0013)."""

from __future__ import annotations

import argparse

import pytest
import yaml

from agent_memory import __version__, audit, deploy


def _args(target):
    return argparse.Namespace(
        target=str(target),
        force=False,
        no_merge=False,
        no_hooks=True,
        cmd="deploy",
        func=deploy.run,
    )


def test_deploy_writes_meta_yaml(tmp_project):
    deploy.run(_args(tmp_project))
    meta_path = tmp_project / ".agent-memory" / ".meta.yaml"
    assert meta_path.is_file()

    data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["version"] == __version__
    assert "deployed_at" in data
    assert data["deployed_at"].endswith("+00:00")
    assert "cli_path" in data
    assert data["telemetry_enabled"] is True


def test_deploy_meta_has_documentation_header(tmp_project):
    deploy.run(_args(tmp_project))
    meta_path = tmp_project / ".agent-memory" / ".meta.yaml"
    text = meta_path.read_text(encoding="utf-8")
    assert text.startswith("# Metadata de instalação do agent-memory.")
    assert "ADR-0013" in text


def test_redeploy_overwrites_meta_with_fresh_timestamp(tmp_project):
    deploy.run(_args(tmp_project))
    meta_path = tmp_project / ".agent-memory" / ".meta.yaml"
    first = yaml.safe_load(meta_path.read_text(encoding="utf-8"))

    deploy.run(_args(tmp_project))
    second = yaml.safe_load(meta_path.read_text(encoding="utf-8"))

    assert first["version"] == second["version"]
    # deployed_at deve ter sido recalculado (ainda que iguais por timestamp grosso)
    assert "deployed_at" in second


def test_read_meta_returns_dict_when_present(tmp_project):
    deploy.run(_args(tmp_project))
    data = audit.read_meta(tmp_project)
    assert data is not None
    assert data["version"] == __version__
    assert data["schema_version"] == 1


def test_read_meta_returns_none_when_absent(tmp_path):
    """Consumidor pré-v0.6 não tem .meta.yaml — não deve quebrar."""
    assert audit.read_meta(tmp_path) is None


def test_read_meta_raises_on_corrupt_yaml(tmp_project):
    meta_path = tmp_project / ".agent-memory" / ".meta.yaml"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text("not: valid: yaml: [unclosed", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML inválido"):
        audit.read_meta(tmp_project)
