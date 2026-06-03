"""constraints.py — Checkers declarativos para constraints da constituição.

Cada constraint em `AGENTS.md` pode declarar um bloco `check` opcional no
frontmatter. Sem ele, a constraint é puramente declarativa (back-compat).
Com ele, `agent-memory audit` executa o checker correspondente e emite
`Issue`s herdando a `severity` da constraint (hard→error, soft→warning).

O conjunto de checkers é FECHADO e genérico — o projeto compõe restrições
via YAML, sem escrever Python. Isso resolve a razão que adiou o item
("cada regra exige um validador"): a expressividade é limitada a globs,
regex e manifestos de dependência. ADR-0028.

Vive em `governance/` (não em `memory/schemas.py`) porque executar um
checker varre a árvore do repositório — governança, não validação de
schema. ADR-0021: governance ⇒ memory é permitido, então importamos
`memory.schemas.Issue`; o inverso seria proibido.

Tudo stdlib + pyyaml (C2 preservada): pathlib.glob, re, tomllib/json.
Agnóstico de linguagem — o checker `dependencies` cobre pyproject.toml,
requirements*.txt e package.json.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from agent_memory.memory.schemas import Issue


# Diretórios nunca varridos pelos checkers de path/pattern. Conservador:
# artefatos de build, caches e VCS não são "código do projeto".
DEFAULT_EXCLUDE_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "dist", "build", ".eggs", ".idea", ".vscode",
}

# Params obrigatórios por tipo de checker. `dependencies` exige `manifest`
# aqui e, adicionalmente, ao menos um de allow/forbid (validado à parte).
REQUIRED_PARAMS: dict[str, set[str]] = {
    "forbid_paths":    {"globs"},
    "require_paths":   {"globs"},
    "forbid_pattern":  {"globs", "pattern"},
    "require_pattern": {"globs", "pattern"},
    "dependencies":    {"manifest"},
}


# --- helpers ---------------------------------------------------------------

def _is_str_list(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _iter_matching(root: Path, globs: list[str], exclude: list[str]):
    """Itera (path, relposix) dos arquivos que casam `globs` sob `root`.

    Pula `DEFAULT_EXCLUDE_DIRS` por componente de caminho e qualquer
    `relposix` que case um glob de `exclude`. Deduplica entre globs.
    """
    seen: set[str] = set()
    for pattern in globs:
        for p in root.glob(pattern):
            if not p.is_file():
                continue
            try:
                rel = p.relative_to(root)
            except ValueError:
                continue
            if set(rel.parts) & DEFAULT_EXCLUDE_DIRS:
                continue
            relposix = rel.as_posix()
            if exclude and any(fnmatch.fnmatch(relposix, ex) for ex in exclude):
                continue
            if relposix in seen:
                continue
            seen.add(relposix)
            yield p, relposix


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _norm_dep(name: str) -> str:
    """Normaliza nome de pacote (PEP 503-ish): minúsculas, `_`/`.` → `-`."""
    return str(name).strip().lower().replace("_", "-").replace(".", "-")


def _pep508_name(spec: str) -> str:
    """Extrai o nome do pacote de uma spec PEP 508 ('pyyaml>=6.0' → 'pyyaml')."""
    m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", str(spec))
    return m.group(1) if m else ""


def _parse_dependencies(path: Path) -> set[str]:
    name = path.name.lower()
    if name == "pyproject.toml":
        return _deps_pyproject(path)
    if name == "package.json":
        return _deps_package_json(path)
    if name.endswith(".txt"):  # requirements*.txt
        return _deps_requirements(path)
    raise ValueError(f"formato de manifest não suportado: {path.name}")


def _deps_pyproject(path: Path) -> set[str]:
    import tomllib
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    # Só dependências de runtime (`[project].dependencies`) — o que o pipx
    # instala. Optional/dev (pytest) ficam fora por design.
    raw = (data.get("project") or {}).get("dependencies") or []
    return {n for s in raw if (n := _pep508_name(s))}


def _deps_requirements(path: Path) -> set[str]:
    text = _read_text(path) or ""
    deps: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        n = _pep508_name(line)
        if n:
            deps.add(n)
    return deps


def _deps_package_json(path: Path) -> set[str]:
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    return set((data.get("dependencies") or {}).keys())


# --- checkers (cada um retorna list[str] de descrições de violação) --------

def _check_forbid_paths(check: dict, root: Path) -> list[str]:
    excl = check.get("exclude") or []
    hits = sorted(rel for _, rel in _iter_matching(root, check["globs"], excl))
    return [f"arquivo proibido existe: {h}" for h in hits]


def _check_require_paths(check: dict, root: Path) -> list[str]:
    excl = check.get("exclude") or []
    found = next(_iter_matching(root, check["globs"], excl), None)
    if found is None:
        return [f"nenhum arquivo casa {check['globs']} (exigido por require_paths)"]
    return []


def _check_forbid_pattern(check: dict, root: Path) -> list[str]:
    excl = check.get("exclude") or []
    rx = re.compile(check["pattern"])
    out: list[str] = []
    for p, rel in _iter_matching(root, check["globs"], excl):
        text = _read_text(p)
        if text is not None and rx.search(text):
            out.append(f"padrão proibido /{check['pattern']}/ encontrado em {rel}")
    return sorted(out)


def _check_require_pattern(check: dict, root: Path) -> list[str]:
    excl = check.get("exclude") or []
    rx = re.compile(check["pattern"])
    out: list[str] = []
    for p, rel in _iter_matching(root, check["globs"], excl):
        text = _read_text(p)
        if text is None or not rx.search(text):
            out.append(f"padrão exigido /{check['pattern']}/ ausente em {rel}")
    return sorted(out)


def _check_dependencies(check: dict, root: Path) -> list[str]:
    manifest = check["manifest"]
    mpath = root / manifest
    if not mpath.exists():
        return [f"manifest de dependências não encontrado: {manifest}"]
    try:
        deps = _parse_dependencies(mpath)
    except Exception as e:  # noqa: BLE001 — parse de formato externo, fail-soft
        return [f"falha ao parsear {manifest}: {e}"]

    out: list[str] = []
    allow = check.get("allow")
    forbid = check.get("forbid")
    if allow is not None:
        allowset = {_norm_dep(a) for a in allow}
        for d in sorted(deps):
            if _norm_dep(d) not in allowset:
                out.append(f"dependência fora da allowlist: {d}")
    if forbid is not None:
        forbidset = {_norm_dep(f) for f in forbid}
        for d in sorted(deps):
            if _norm_dep(d) in forbidset:
                out.append(f"dependência proibida: {d}")
    return out


CHECKERS = {
    "forbid_paths":    _check_forbid_paths,
    "require_paths":   _check_require_paths,
    "forbid_pattern":  _check_forbid_pattern,
    "require_pattern": _check_require_pattern,
    "dependencies":    _check_dependencies,
}


# --- shape validation + runner ---------------------------------------------

def validate_check_shape(check) -> list[str]:
    """Valida a forma de um bloco `check`. Retorna lista de problemas (vazia=ok)."""
    if not isinstance(check, dict):
        return ["bloco 'check' deve ser um mapping"]
    ctype = check.get("type")
    if ctype is None:
        return ["campo 'type' ausente"]
    if ctype not in CHECKERS:
        return [f"type desconhecido '{ctype}' (esperado: {sorted(CHECKERS)})"]

    problems: list[str] = []
    for field in REQUIRED_PARAMS[ctype]:
        if field not in check:
            problems.append(f"type={ctype} requer '{field}'")

    if "globs" in check and not _is_str_list(check.get("globs")):
        problems.append("'globs' deve ser lista de strings")
    if "exclude" in check and not _is_str_list(check.get("exclude")):
        problems.append("'exclude' deve ser lista de strings")
    if "pattern" in check:
        pat = check.get("pattern")
        if not isinstance(pat, str):
            problems.append("'pattern' deve ser string")
        else:
            try:
                re.compile(pat)
            except re.error as e:
                problems.append(f"'pattern' é regex inválido: {e}")

    if ctype == "dependencies":
        if "manifest" in check and not isinstance(check.get("manifest"), str):
            problems.append("'manifest' deve ser string")
        if check.get("allow") is None and check.get("forbid") is None:
            problems.append("dependencies requer 'allow' e/ou 'forbid'")
        for k in ("allow", "forbid"):
            if check.get(k) is not None and not _is_str_list(check.get(k)):
                problems.append(f"'{k}' deve ser lista de strings")

    return problems


def check_constraints(agent_fm: dict, root: Path) -> dict:
    """Executa os checkers de todas as constraints com bloco `check`.

    Retorna {"issues": list[Issue], "checked": int, "violations": int}.
    `checked` conta constraints com `check` bem-formado executadas;
    `violations` conta Issues de violação (não erros de forma do `check`).
    """
    issues: list[Issue] = []
    checked = 0
    violations = 0

    constraints = agent_fm.get("constraints")
    if not isinstance(constraints, list):
        return {"issues": issues, "checked": checked, "violations": violations}

    for c in constraints:
        if not isinstance(c, dict):
            continue
        check = c.get("check")
        if not check:
            continue
        cid = c.get("id", "?")

        problems = validate_check_shape(check)
        if problems:
            for p in problems:
                issues.append(Issue(
                    "AGENTS.md", "error",
                    f"constraint {cid}: check inválido — {p}",
                ))
            continue

        checked += 1
        fn = CHECKERS[check["type"]]
        try:
            viols = fn(check, root)
        except Exception as e:  # noqa: BLE001 — checker não deve derrubar o audit
            issues.append(Issue(
                "AGENTS.md", "error",
                f"constraint {cid}: checker '{check['type']}' falhou — {e}",
            ))
            continue

        sev = "error" if c.get("severity") == "hard" else "warning"
        for v in viols:
            violations += 1
            issues.append(Issue("AGENTS.md", sev, f"constraint {cid} violada: {v}"))

    return {"issues": issues, "checked": checked, "violations": violations}
