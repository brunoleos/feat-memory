"""version_check.py — Notice soft quando consumer está desatualizado.

Lê `.agent-memory/.meta.yaml::version` e compara a `agent_memory.__version__`.
Se diferentes, retorna texto sugerindo `agent-memory deploy .`.

Subcomando: `agent-memory version-check` (standalone, para CI/scripts).
Integração: `governance.audit::run` invoca após `print_report` e imprime
na stderr (não muda exit code — soft, ADR-0008).

ADR-0022 documenta política. Disable via `.meta.yaml::version_check_enabled: false`.

Parte de `governance/`. Importa apenas de `shared/` e `agent_memory.__version__`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_memory import __version__
from agent_memory.shared import paths as _paths
from agent_memory.shared.parsing import read_meta


NOTICE_TEMPLATE = (
    "ℹ agent-memory CLI {cli} vs deployed {deployed}\n"
    "  re-rode `agent-memory deploy .` para sincronizar skills/templates\n"
    "  (mudanças nesta versão podem afetar como o agente carrega contexto)."
)

UP_TO_DATE_TEMPLATE = "✓ agent-memory atualizado (v{cli})"


def consumer_version_notice(root: Path) -> str | None:
    """Retorna texto do notice se versões diferem, ou None.

    Casos onde retorna None (fail-soft):
    - `.meta.yaml` ausente (consumer pré-v0.6, ou root inválido)
    - `meta.get("version")` ausente ou vazio
    - `meta.get("version_check_enabled") is False`
    - Versões iguais
    """
    meta = read_meta(root)
    if not meta:
        return None
    if meta.get("version_check_enabled") is False:
        return None
    deployed = meta.get("version")
    if not deployed:
        return None
    if str(deployed) == str(__version__):
        return None
    return NOTICE_TEMPLATE.format(cli=__version__, deployed=deployed)


def _print_notice(text: str) -> None:
    """Imprime na stderr (amarelo com isatty, plain em CI)."""
    if sys.stderr.isatty():
        print(f"\033[33m{text}\033[0m", file=sys.stderr)
    else:
        print(text, file=sys.stderr)


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "version-check",
        help="Notice se a versão do CLI difere de .agent-memory/.meta.yaml::version "
             "(soft, sempre exit 0; ADR-0022)",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    _paths._init_paths()
    notice = consumer_version_notice(_paths.ROOT)
    if notice:
        _print_notice(notice)
    else:
        print(UP_TO_DATE_TEMPLATE.format(cli=__version__))
    return 0
