"""Guard estrutural contra a classe de bug "stale-on-cutover".

Recorreu várias vezes: skills/templates shipados citando comandos/arquivos
REMOVIDOS (`migrate --to=changelog`, `feat-memory checkpoint`, `suggestions.md`,
`STATE.md` como artefato vivo) depois de uma reforma. O dogfood do cliente é que
pegava — este teste pega antes de shipar.

Escopo: as superfícies que o consumidor recebe e lê (skills/ + data/templates +
data/skills + data/agents). Devem estar 100% no layout atual. O CÓDIGO não é
escaneado — ele legitimamente mantém retrocompat (ex.: validar um STATE.md legado).
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SURFACES = [REPO / "skills", REPO / "src" / "feat_memory" / "data"]

# Comandos/arquivos REMOVIDOS — não há uso legítimo vivo numa superfície shipada.
REMOVED_TOKENS = [
    "migrate --to=changelog",   # comando removido (2.3.0)
    "feat-memory checkpoint",   # comando removido (2.0.0)
    "feat-memory state-rebuild",
    "state-rebuild",
    "suggestions.md",           # renomeado p/ ideas.md (2.2.0)
    "deploy_suggestions",
]


def _shipped_files():
    for base in SURFACES:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.suffix in (".md", ".py", "") and "__pycache__" not in p.parts and p.is_file():
                yield p


def test_shipped_surfaces_have_no_removed_symbols():
    offenders = []
    for p in _shipped_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for tok in REMOVED_TOKENS:
            if tok in text:
                offenders.append(f"{p.relative_to(REPO)}: '{tok}'")
    assert not offenders, (
        "Referência a símbolo removido em superfície shipada (stale-on-cutover):\n  "
        + "\n  ".join(offenders)
    )
