"""Anti-regressão de package-data (F-0021).

Garante que todo arquivo de *data* exigido em runtime — pre-commit hook,
templates, skills — está coberto por algum glob declarado em
`[tool.setuptools.package-data]`. Esse teste teria pego o bug do split
F-0017, em que o hook migrou para `governance/data/hooks/` mas o
package-data continuou apontando para `data/hooks/*` (inexistente), de
modo que o wheel publicado na PyPI omitiria o hook. ADR-0025.

Rápido e sem build: valida a declaração contra a árvore-fonte, não um
wheel construído.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"


def _package_data() -> dict[str, list[str]]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        data = tomllib.load(fh)
    return data["tool"]["setuptools"]["package-data"]


def _pkg_dir(pkg: str) -> Path:
    """feat_memory.governance -> src/feat_memory/governance."""
    return SRC.joinpath(*pkg.split("."))


def _matches(pkg: str, pattern: str) -> list[Path]:
    return list(_pkg_dir(pkg).glob(pattern))


# Arquivos de data exigidos em runtime (resolvidos por deploy._data_path).
RUNTIME_DATA = [
    ("feat_memory.governance", "data/hooks/pre-commit"),
    ("feat_memory", "data/templates/AGENTS.md"),
    ("feat_memory", "data/templates/CLAUDE.md"),
    ("feat_memory", "data/templates/ideas.md"),
    ("feat_memory", "data/templates/AGENTS.frontmatter-skeleton.md"),
    ("feat_memory", "data/templates/.gitattributes"),
]


def test_every_declared_glob_matches_at_least_one_file():
    """Glob declarado que não casa nada é package-data morto (o bug)."""
    pkg_data = _package_data()
    for pkg, patterns in pkg_data.items():
        for pattern in patterns:
            assert _matches(pkg, pattern), (
                f"package-data {pkg!r} declara {pattern!r} mas nenhum "
                f"arquivo casa em {_pkg_dir(pkg)}"
            )


@pytest.mark.parametrize("pkg,rel", RUNTIME_DATA)
def test_runtime_data_is_covered_by_some_glob(pkg: str, rel: str):
    """Cada arquivo de runtime existe E é coberto por um glob declarado."""
    target = _pkg_dir(pkg) / rel
    assert target.is_file(), f"arquivo de runtime ausente: {target}"

    patterns = _package_data().get(pkg, [])
    covered = any(target in _matches(pkg, pat) for pat in patterns)
    assert covered, (
        f"{pkg}:{rel} existe mas nenhum glob de package-data o inclui — "
        f"seria omitido do wheel"
    )


def test_every_skill_is_covered():
    """Todo SKILL.md em data/skills/ entra no wheel."""
    skills_dir = _pkg_dir("feat_memory") / "data" / "skills"
    patterns = _package_data()["feat_memory"]
    for skill in skills_dir.glob("*/SKILL.md"):
        covered = any(skill in _matches("feat_memory", pat) for pat in patterns)
        assert covered, f"skill não coberto por package-data: {skill}"
