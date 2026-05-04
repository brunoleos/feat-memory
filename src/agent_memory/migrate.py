"""
migrate.py — Assistente de migração para projetos legados.

Examina o histórico do Git e propõe ADRs candidatos a partir de mensagens
de commit que sugerem decisões arquiteturais. Detecta também a stack
principal do projeto a partir de arquivos de manifesto comuns.

Importante: este script não escreve nada automaticamente. Todas as
sugestões são impressas para revisão humana, porque gênese retroativa
silenciosa cristaliza interpretações erradas como decisões oficiais.

Subcomando da CLI: `agent-memory migrate`. O project root é descoberto
via git rev-parse.

Uso:
    agent-memory migrate              # últimos 100 commits
    agent-memory migrate --limit 200  # mais commits
    agent-memory migrate --json       # output estruturado
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _run_to_checkpoints() -> int:
    """Cria o primeiro checkpoint a partir de STATE.md legado.

    Idempotente: se .agent-memory/checkpoints/ já tem arquivos, retorna 0
    sem mexer. Não-destrutivo: o STATE.md original é preservado (regerado
    com mesmo conteúdo, agora derivado do checkpoint). ADR-0019.
    """
    from agent_memory import audit, checkpoints as cp

    audit._init_paths()
    cp_dir = cp._checkpoints_dir(audit.ROOT)
    if cp_dir.exists() and any(cp_dir.glob("*.md")):
        print("Checkpoints já existem em .agent-memory/checkpoints/. "
              "Migração é idempotente — nada a fazer.")
        return 0

    state_path = cp._state_path(audit.ROOT)
    if not state_path.exists():
        print("STATE.md não existe em .agent-memory/. "
              "Crie um com `agent-memory deploy` ou rode "
              "`agent-memory checkpoint --summary '...'` direto.",
              file=sys.stderr)
        return 1

    try:
        fm, body = audit.parse_frontmatter(state_path)
    except ValueError as e:
        print(f"ERRO ao ler STATE.md: {e}", file=sys.stderr)
        return 1

    current = _extract_section(body, "Current") or "(não detectado em STATE.md legado)"
    next_ = _extract_section(body, "Next") or "TODO"
    summary = f"{current} | next: {next_}"

    ts_raw = fm.get("updated_at")
    now = None
    if ts_raw:
        try:
            from datetime import datetime, timezone
            s = str(ts_raw).replace("Z", "+00:00")
            now = datetime.fromisoformat(s)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
        except ValueError:
            now = None

    cp_path = cp.append_checkpoint(
        audit.ROOT,
        summary=summary,
        current=current,
        next_=next_,
        features=list(fm.get("active_features") or []),
        decisions=list(fm.get("active_decisions") or []),
        blocked_on=fm.get("blocked_on"),
        author=str(fm.get("updated_by") or "migration"),
        body=f"_(corpo preservado do STATE.md legado durante migração)_\n\n{body.strip()}\n",
        now=now,
    )
    state_new = cp.write_state(audit.ROOT)

    rel_cp = cp_path.relative_to(audit.ROOT)
    rel_st = state_new.relative_to(audit.ROOT)
    print("✓ migração concluída.")
    print(f"  checkpoint inicial: {rel_cp}")
    print(f"  STATE.md regerado:  {rel_st}")
    print()
    print("A partir daqui, use `agent-memory checkpoint --summary '...'` "
          "(ou a skill memory-debrief) para registrar novas sessões.")
    return 0


def _extract_section(body: str, name: str) -> str | None:
    """Pega a primeira linha não-vazia da seção H2 indicada."""
    pattern = re.compile(rf"^##\s+{re.escape(name)}\s*$", re.MULTILINE)
    m = pattern.search(body)
    if not m:
        return None
    rest = body[m.end():]
    next_h = re.search(r"^##\s", rest, re.MULTILINE)
    section = rest[:next_h.start()] if next_h else rest
    for line in section.splitlines():
        s = line.strip()
        if s:
            return s
    return None


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


def detect_entry_points(root: Path) -> list[str]:
    """Sugere candidatos a entrypoints públicos para virar features."""
    candidates: list[str] = []
    patterns = [
        ("APIs HTTP", ["**/routes/*.py", "**/api/*.py", "**/handlers/*.py",
                       "**/controllers/*.py"]),
        ("Comandos CLI", ["**/cli/*.py", "**/commands/*.py", "**/__main__.py"]),
        ("Casos de uso", ["**/use_cases/*.py", "**/usecases/*.py",
                          "**/services/*.py"]),
    ]
    for label, globs in patterns:
        files: list[Path] = []
        for g in globs:
            files.extend(root.glob(g))
        if files:
            candidates.append(f"{label}: {len(files)} arquivos encontrados")
    return candidates


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "migrate",
        help="Examina histórico Git e sugere ADRs candidatos para projetos legados",
    )
    p.add_argument("--limit", type=int, default=100,
                   help="número de commits a examinar (padrão: 100)")
    p.add_argument("--json", action="store_true",
                   help="output em JSON")
    p.add_argument("--to", choices=["checkpoints"], default=None,
                   help="modo de migração explícita (ex: --to=checkpoints "
                        "cria primeiro checkpoint a partir do STATE.md legado; "
                        "ADR-0019)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    if getattr(args, "to", None) == "checkpoints":
        return _run_to_checkpoints()

    root = find_project_root()

    try:
        commits = git_log(args.limit)
    except subprocess.CalledProcessError:
        print("Erro: não é um repositório Git ou git não está no PATH",
              file=sys.stderr)
        return 1

    stack = detect_stack(root)
    candidates = suggest_decisions(commits)
    entry_points = detect_entry_points(root)

    if args.json:
        print(json.dumps({
            "commits_analyzed": len(commits),
            "stack_detected": stack,
            "decision_candidates": [
                {"sha": s, "message": m, "label": l}
                for s, m, l in candidates
            ],
            "entry_point_signals": entry_points,
        }, indent=2, ensure_ascii=False))
        return 0

    print("=" * 60)
    print("Sugestões de migração")
    print("=" * 60)

    if stack:
        print("\nStack detectada:")
        for s in stack:
            print(f"  • {s}")
        print("→ Adicione em AGENT.md::stack")
    else:
        print("\nNenhuma stack reconhecida automaticamente.")

    print(f"\nCommits analisados: {len(commits)}")
    if candidates:
        print(f"\n{len(candidates)} possíveis ADRs candidatos:")
        for sha, msg, label in candidates:
            print(f"  [{label:>22}] {sha} {msg}")
    else:
        print("\nNenhum padrão de decisão detectado nas mensagens de commit.")

    if entry_points:
        print("\nEntrypoints candidatos a virar features:")
        for ep in entry_points:
            print(f"  • {ep}")
    else:
        print("\nNenhum entrypoint padrão detectado.")

    print("\n" + "=" * 60)
    print("Próximos passos:")
    print("  1. Revisar candidatos acima.")
    print("  2. Para cada ADR relevante, criar .agent-memory/decisions/NNNN-slug.md.")
    print("  3. Para cada entrypoint público, criar arquivo em")
    print("     .agent-memory/manifest/features/F-NNNN-slug.md com status: shipped.")
    print("  4. Rodar `agent-memory audit` para validar e gerar índices.")
    return 0
