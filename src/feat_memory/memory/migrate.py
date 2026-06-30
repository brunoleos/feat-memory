"""
migrate.py — Assistente de migração para projetos legados.

Gera PISTAS para a gênese retroativa, na ordem de precisão para inferir
propósito (ADR-0030, ADR-0031), todas agnósticas de linguagem:
1. **Testes** (`detect_test_signals`) — a fonte mais precisa de comportamento
   pretendido; spec executável.
2. **UI/telas** (`detect_ui_signals`) — o mapa de capacidades como o usuário
   as vê.
3. **Entrypoints** (`detect_entry_points`) — a superfície pública; verdade do
   comportamento, propósito por inferência.
4. **Stack** (`detect_stack`) — a partir de arquivos de manifesto comuns.
5. **Git log** (`suggest_decisions`) — fonte secundária; mensagens de commit
   que datam/justificam decisões já identificadas no código, não as originam.

O agente/skill não deve parar nestas pistas: a análise de verdade é a leitura
e triangulação das fontes. Esta ferramenta só aponta onde olhar.

Importante: este script não escreve nada automaticamente. Todas as
sugestões são impressas para revisão humana, porque gênese retroativa
silenciosa cristaliza interpretações erradas como decisões oficiais.

Subcomando da CLI: `feat-memory migrate`. O project root é descoberto
via git rev-parse.

Uso:
    feat-memory migrate              # últimos 100 commits
    feat-memory migrate --limit 200  # mais commits
    feat-memory migrate --json       # output estruturado
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path:
    """Descobre o project root via git, com fallback."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return Path.cwd()


DECISION_PATTERNS: list[tuple[str, str]] = [
    (r"\brevert(?:s|ed|ing)?\b", "reverted"),
    (r"\binstead of\b", "alternative-rejected"),
    (r"\bswitch(?:ed)?\s+from\b", "alternative-rejected"),
    (r"\bdecid(?:ed|e)\s+to\b", "explicit-decision"),
    (r"\breplac(?:ed|e)\s+\w+\s+with\b", "replacement"),
    (r"\bmigrat(?:ed|e)\s+from\b", "replacement"),
    (r"\bdeprecat(?:ed|e)\b", "deprecation"),
    (r"\bremov(?:ed|e)\s+\w+\s+support\b", "scope-reduction"),
]

STACK_SIGNALS: dict[str, list[str]] = {
    "Python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
    "Node.js / TypeScript": ["package.json", "tsconfig.json"],
    "Rust": ["Cargo.toml"],
    "Go": ["go.mod"],
    "Java / Kotlin": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "Ruby": ["Gemfile"],
    "Elixir": ["mix.exs"],
    "PHP": ["composer.json"],
}


def git_log(limit: int) -> list[tuple[str, str]]:
    """Retorna lista de (sha curto, mensagem) dos últimos N commits."""
    out = subprocess.check_output(
        ["git", "log", f"-{limit}", "--pretty=format:%h\t%s"],
        text=True,
    )
    return [tuple(line.split("\t", 1)) for line in out.splitlines()
            if "\t" in line]


def suggest_decisions(
    commits: list[tuple[str, str]],
) -> list[tuple[str, str, str]]:
    """Identifica commits que sugerem decisões arquiteturais."""
    candidates: list[tuple[str, str, str]] = []
    for sha, msg in commits:
        for pattern, label in DECISION_PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                candidates.append((sha, msg, label))
                break
    return candidates


def detect_stack(root: Path) -> list[str]:
    """Detecta linguagens/stacks a partir de arquivos no projeto."""
    detected: list[str] = []
    for lang, files in STACK_SIGNALS.items():
        if any((root / f).exists() for f in files):
            detected.append(lang)
    return detected


# Extensões de fonte reconhecidas — a varredura é agnóstica de linguagem
# (ADR-0030). O `detect_entry_points` antigo só olhava `*.py`, então retornava
# vazio em projetos JS/TS/Go/etc. e o agente perdia o sinal de onde olhar.
SOURCE_EXTS: set[str] = {
    ".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".go", ".rs",
    ".rb", ".java", ".kt", ".ex", ".exs", ".php",
}

# Diretórios de convenção onde entrypoints públicos costumam morar.
ENTRY_POINT_DIRS: set[str] = {
    "routes", "api", "handlers", "controllers", "endpoints",
    "cli", "commands", "bin",
    "use_cases", "usecases", "services", "pages", "views",
}

# Testes: a fonte mais precisa de comportamento PRETENDIDO (ADR-0031). Detectados
# por diretório de convenção e por padrão de nome de arquivo.
TEST_DIR_NAMES: set[str] = {
    "tests", "test", "__tests__", "spec", "specs", "e2e",
    "cypress", "playwright", "integration", "unit",
}
TEST_FILE_RE = re.compile(
    r"(^test_.+|.+_test\.[a-z]+$|.+\.test\.[a-z]+$|.+\.spec\.[a-z]+$)", re.I
)

# UI/telas: o mapa de capacidades como o usuário as vê (ADR-0031).
UI_DIR_NAMES: set[str] = {
    "pages", "views", "screens", "templates", "components", "ui",
}
UI_EXTS: set[str] = {".html", ".vue", ".svelte", ".jsx", ".tsx", ".astro"}

# Podados na varredura — vendored, build e o próprio .feat-memory.
IGNORE_DIRS: set[str] = {
    "node_modules", ".git", ".venv", "venv", "env", "dist", "build",
    "__pycache__", ".feat-memory", "vendor", "target", ".next",
    "coverage", "test-results", "playwright-report", ".mypy_cache",
    ".pytest_cache", "site-packages",
}


def detect_entry_points(root: Path) -> list[str]:
    """Sugere áreas com entrypoints públicos — uma PISTA, não a fonte.

    Language-agnostic: varre diretórios de convenção (`routes/`, `cli/`, …) em
    qualquer extensão de fonte reconhecida, podando vendored/build. É só um
    ponto de partida: a fonte primária da gênese do Manifest é a leitura do
    próprio código (ADR-0030), não esta contagem. O git log é apenas a terceira
    fonte (narrativa do "porquê"), depois do código e dos entrypoints.
    """
    import os

    hits: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        rel = Path(dirpath).relative_to(root)
        parts = {p.lower() for p in rel.parts}
        matched = ENTRY_POINT_DIRS & parts
        if not matched:
            continue
        n = sum(1 for fn in filenames if Path(fn).suffix in SOURCE_EXTS)
        if n:
            for d in matched:
                hits[d] = hits.get(d, 0) + n
    return [f"{d}/: {n} arquivo(s) de fonte" for d, n in sorted(hits.items())]


def detect_test_signals(root: Path) -> list[str]:
    """Aponta onde estão os testes — a fonte mais precisa de uso (ADR-0031).

    Conta arquivos de fonte em diretórios de teste por convenção e, fora deles,
    arquivos cujo nome casa o padrão de teste (`test_*`, `*_test.*`, `*.spec.*`).
    """
    import os

    hits: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        parts = {p.lower() for p in Path(dirpath).relative_to(root).parts}
        in_test_dir = TEST_DIR_NAMES & parts
        if in_test_dir:
            key = sorted(in_test_dir)[0]
            n = sum(1 for fn in filenames if Path(fn).suffix in SOURCE_EXTS)
            if n:
                hits[key] = hits.get(key, 0) + n
        else:
            n = sum(1 for fn in filenames
                    if Path(fn).suffix in SOURCE_EXTS and TEST_FILE_RE.search(fn))
            if n:
                hits["(test_*/*.spec)"] = hits.get("(test_*/*.spec)", 0) + n
    return [f"{k}: {n} arquivo(s) de teste" for k, n in sorted(hits.items())]


def detect_ui_signals(root: Path) -> list[str]:
    """Aponta a camada de UI/telas — o mapa de capacidades visíveis (ADR-0031)."""
    import os

    dir_hits: dict[str, int] = {}
    ext_hits: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        parts = {p.lower() for p in Path(dirpath).relative_to(root).parts}
        for d in UI_DIR_NAMES & parts:
            n = sum(1 for fn in filenames
                    if Path(fn).suffix in (SOURCE_EXTS | UI_EXTS))
            if n:
                dir_hits[d] = dir_hits.get(d, 0) + n
        for fn in filenames:
            ext = Path(fn).suffix
            if ext in UI_EXTS:
                ext_hits[ext] = ext_hits.get(ext, 0) + 1
    out = [f"{d}/: {n} arquivo(s)" for d, n in sorted(dir_hits.items())]
    if ext_hits:
        exts = ", ".join(f"{e} ({n})" for e, n in sorted(ext_hits.items()))
        out.append(f"arquivos de view: {exts}")
    return out


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "migrate",
        help="Examina histórico Git e sugere ADRs candidatos para projetos legados",
    )
    p.add_argument("path", nargs="?", default=None,
                   help="raiz do projeto (default: descobre via git/cwd)")
    p.add_argument("--limit", type=int, default=100,
                   help="número de commits a examinar (padrão: 100)")
    p.add_argument("--json", action="store_true",
                   help="output em JSON")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    explicit = Path(args.path).resolve() if getattr(args, "path", None) else None
    root = explicit if explicit is not None else find_project_root()

    try:
        commits = git_log(args.limit)
    except subprocess.CalledProcessError:
        print("Erro: não é um repositório Git ou git não está no PATH",
              file=sys.stderr)
        return 1

    stack = detect_stack(root)
    candidates = suggest_decisions(commits)
    test_signals = detect_test_signals(root)
    ui_signals = detect_ui_signals(root)
    entry_points = detect_entry_points(root)

    if args.json:
        print(json.dumps({
            "commits_analyzed": len(commits),
            "stack_detected": stack,
            "test_signals": test_signals,
            "ui_signals": ui_signals,
            "entry_point_signals": entry_points,
            "decision_candidates": [
                {"sha": s, "message": m, "label": l}
                for s, m, l in candidates
            ],
        }, indent=2, ensure_ascii=False))
        return 0

    print("=" * 60)
    print("Sugestões de migração — fontes em ordem de precisão (ADR-0031)")
    print("=" * 60)

    if stack:
        print("\nStack detectada:")
        for s in stack:
            print(f"  • {s}")
        print("→ Adicione em AGENTS.md::stack")
    else:
        print("\nNenhuma stack reconhecida automaticamente.")

    # Fonte mais precisa de comportamento pretendido: os testes.
    if test_signals:
        print("\n[1] TESTES (a spec executável — LEIA PRIMEIRO):")
        for t in test_signals:
            print(f"  • {t}")
        print("  → nomes de cenário ≈ features; asserções ≈ critérios acceptance.")
    else:
        print("\n[1] Nenhum teste detectado — sem a fonte mais precisa de uso; "
              "triangule telas + docs + código com mais cuidado.")

    # As telas mostram as capacidades como o usuário as vê.
    if ui_signals:
        print("\n[2] UI / TELAS (mapa de capacidades visíveis):")
        for u in ui_signals:
            print(f"  • {u}")
        print("  → cada tela/rota ≈ capacidade; labels/i18n nomeiam o user_value.")

    # Fonte da verdade do comportamento; propósito exige inferência.
    if entry_points:
        print("\n[3] ENTRYPOINTS (superfície pública — confirme comportamento):")
        for ep in entry_points:
            print(f"  • {ep}")
    else:
        print("\n[3] Nenhum diretório de entrypoint por convenção — "
              "leia os exports/main reais do projeto.")

    # Fonte secundária: o git log só agrega o "porquê/quando" de decisões.
    print(f"\n[4] GIT — {len(commits)} commits analisados (fonte secundária):")
    if candidates:
        print(f"  {len(candidates)} com pistas de DECISÃO "
              "(corrobora/data ADRs, não os origina):")
        for sha, msg, label in candidates:
            print(f"    [{label:>22}] {sha} {msg}")
    else:
        print("  Nenhum padrão de decisão nas mensagens "
              "(normal em histórico squashado — não é bloqueio).")

    print("\n" + "=" * 60)
    print("Próximos passos (engenharia reversa multi-fonte — ADR-0030/0031):")
    print("  1. TRIANGULE as fontes acima (testes+telas+docs+código): só")
    print("     cristalize o que ≥2 fontes confirmam; marque o resto como")
    print("     hipótese de baixa confiança para revisão humana.")
    print("  2. Para cada capacidade, criar F-NNNN-slug.md (status: shipped),")
    print("     com acceptance EARS derivado das asserções dos testes.")
    print("  3. Para cada decisão (deps/estrutura/camadas; git data/justifica),")
    print("     criar .feat-memory/decisions/NNNN-slug.md.")
    print("  4. Rodar `feat-memory audit` para validar e gerar índices.")
    return 0
