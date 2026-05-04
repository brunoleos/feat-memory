"""cli.py — Entrypoint da CLI agent-memory.

Despacha argv para o subcomando apropriado. Cada módulo registra seu
próprio subparser via add_subparser(subparsers).
"""

from __future__ import annotations

import argparse
import sys

from agent_memory import __version__, archive, audit, deploy, migrate, propose_adr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-memory",
        description="Persistent memory methodology for LLM agents.",
    )
    parser.add_argument(
        "--version", action="version", version=f"agent-memory {__version__}",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    deploy.add_subparser(sub)
    audit.add_subparser(sub)
    propose_adr.add_subparser(sub)
    migrate.add_subparser(sub)
    archive.add_subparser(sub)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
