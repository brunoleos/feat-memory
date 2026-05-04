"""
audit.py — Auditoria dos quatro artefatos de memória do projeto.

Valida schemas, gera índices e produz relatório de saúde.

Subcomando da CLI: `agent-memory audit`. AGENT.md fica na raiz do
project root; STATE.md, manifest/ e decisions/ ficam em .agent-memory/.
O project root é descoberto via `git rev-parse --show-toplevel`.

Uso:
    agent-memory audit              # relatório + índices
    agent-memory audit --json       # output em JSON (CI)
    agent-memory audit --strict     # warnings viram errors
    agent-memory audit --no-index   # só valida

Saída:
    Exit code 0 se nenhum erro foi encontrado.
    Exit code 1 se houve erro de schema, ou drift em modo --strict.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

def _yaml():
    """Importa PyYAML preguiçosamente com mensagem de erro acionável.

    Retorna o módulo `yaml`. Sai com exit 1 se PyYAML não está instalado.
    Adiar o import até a primeira chamada evita que `agent-memory --help`
    (que não toca em YAML) pague o custo de carregar a lib.
    """
    try:
        import yaml as _y
    except ImportError:
        print(
            "ERRO: PyYAML é uma dependência obrigatória.\n\n"
            "Instale com um dos comandos abaixo:\n"
            "  pip install pyyaml\n"
            "  pip3 install pyyaml\n"
            "  python -m pip install pyyaml\n\n"
            "Em ambientes com gerenciamento de pacotes do sistema "
            "(Debian/Ubuntu recente),\n"
            "use --break-system-packages se necessário ou um virtualenv:\n"
            "  pip install --break-system-packages pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)
    return _y


def find_project_root() -> Path:
    """Descobre o project root via git, com fallback para o cwd."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    current = Path.cwd().resolve()
    for _ in range(5):
        if (current / "AGENT.md").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return Path.cwd()


# ROOT/AGENT/etc são populados preguiçosamente via _init_paths() na
# primeira chamada de run(). Importar o módulo (ex.: para registrar o
# subparser via cli.py) não dispara `git rev-parse`.
ROOT: Path = None  # type: ignore[assignment]
AGENT: Path = None  # type: ignore[assignment]
CLAUDE: Path = None  # type: ignore[assignment]
STATE: Path = None  # type: ignore[assignment]
MANIFEST_DIR: Path = None  # type: ignore[assignment]
FEATURES_DIR: Path = None  # type: ignore[assignment]
ARCHIVE_DIR: Path = None  # type: ignore[assignment]
DECISIONS_DIR: Path = None  # type: ignore[assignment]
PROPOSALS_DIR: Path = None  # type: ignore[assignment]


def _init_paths() -> None:
    """Resolve ROOT e dependentes a partir do cwd. Idempotente."""
    global ROOT, AGENT, CLAUDE, STATE
    global MANIFEST_DIR, FEATURES_DIR, ARCHIVE_DIR, DECISIONS_DIR, PROPOSALS_DIR
    if ROOT is not None:
        return
    ROOT = find_project_root()
    AGENT = ROOT / "AGENT.md"
    CLAUDE = ROOT / "CLAUDE.md"
    STATE = ROOT / ".agent-memory" / "STATE.md"
    MANIFEST_DIR = ROOT / ".agent-memory" / "manifest"
    FEATURES_DIR = MANIFEST_DIR / "features"
    ARCHIVE_DIR = MANIFEST_DIR / "archive"
    DECISIONS_DIR = ROOT / ".agent-memory" / "decisions"
    PROPOSALS_DIR = DECISIONS_DIR / "proposals"

FEATURE_FILE_RE = re.compile(r"^F-\d{4}-[a-z0-9-]+\.md$")
DECISION_FILE_RE = re.compile(r"^\d{4}-[a-z0-9-]+\.md$")

VALID_FEATURE_STATUS = {"planned", "in_progress", "shipped", "deprecated"}
VALID_DECISION_STATUS = {"proposed", "accepted", "superseded", "deprecated"}

EARS_PATTERN_FIELDS: dict[str, set[str]] = {
    "ubiquitous": {"requirement"},
    "event":      {"trigger", "response"},
    "state":      {"state", "response"},
    "optional":   {"feature", "response"},
    "unwanted":   {"trigger", "response"},
    "complex":    {"requirement"},
}

DEFAULT_RESUMPTION_BUDGET = 12288
DEFAULT_STATE_BUDGET = 4096


# --- parsing ---------------------------------------------------------------

def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Extrai YAML frontmatter de um arquivo markdown."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    yaml = _yaml()
    try:
        fm = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML inválido em {path}: {e}") from e
    body = text[end + 5:]
    return fm, body


def read_meta(root: Path) -> dict | None:
    """Lê `.agent-memory/.meta.yaml` no consumidor.

    Retorna o dict YAML ou `None` se o arquivo não existe (consumidor
    instalado antes de v0.6.0). Schema definido em ADR-0013. Tolerância
    a ausência é deliberada — chamadores degradam graciosamente.
    """
    path = root / ".agent-memory" / ".meta.yaml"
    if not path.exists():
        return None
    yaml = _yaml()
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML inválido em {path}: {e}") from e


# --- validation ------------------------------------------------------------

@dataclass
class Issue:
    artifact: str
    severity: str  # "error" | "warning"
    message: str


def validate_agent(path: Path) -> tuple[dict, list[Issue]]:
    issues: list[Issue] = []
    if not path.exists():
        return {}, [Issue("AGENT.md", "error", "arquivo ausente")]
    try:
        fm, _ = parse_frontmatter(path)
    except ValueError as e:
        return {}, [Issue("AGENT.md", "error", str(e))]
    required = ["schema_version", "project", "constraints", "references", "budgets"]
    for key in required:
        if key not in fm:
            issues.append(Issue("AGENT.md", "error", f"campo ausente: {key}"))
    return fm, issues


def validate_state(path: Path, max_bytes: int) -> tuple[dict, list[Issue]]:
    issues: list[Issue] = []
    if not path.exists():
        return {}, [Issue("STATE.md", "error", "arquivo ausente")]
    size = path.stat().st_size
    if size > max_bytes:
        issues.append(Issue(
            "STATE.md", "error",
            f"tamanho {size}B excede orçamento de {max_bytes}B",
        ))
    try:
        fm, _ = parse_frontmatter(path)
    except ValueError as e:
        return {}, [Issue("STATE.md", "error", str(e))]
    required = ["schema_version", "updated_at", "active_features"]
    for key in required:
        if key not in fm:
            issues.append(Issue("STATE.md", "error", f"campo ausente: {key}"))
    return fm, issues


def _collect_contract_paths(contracts: dict) -> list[str]:
    paths: list[str] = []
    for key in ("api", "schemas", "tests"):
        val = contracts.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            paths.append(val)
        elif isinstance(val, list):
            paths.extend(str(p) for p in val)
        elif isinstance(val, dict):
            paths.extend(str(p) for p in val.values())
    return paths


def validate_ears_criterion(name: str, idx: int,
                            criterion: dict) -> list[Issue]:
    issues: list[Issue] = []
    cid = criterion.get("id", f"#{idx}")
    pattern = criterion.get("pattern")

    if not pattern:
        issues.append(Issue(
            name, "error",
            f"acceptance[{cid}]: campo 'pattern' ausente "
            f"(esperado: {sorted(EARS_PATTERN_FIELDS)})",
        ))
        return issues

    if pattern not in EARS_PATTERN_FIELDS:
        issues.append(Issue(
            name, "error",
            f"acceptance[{cid}]: pattern inválido '{pattern}' "
            f"(esperado: {sorted(EARS_PATTERN_FIELDS)})",
        ))
        return issues

    required = EARS_PATTERN_FIELDS[pattern]
    for field in required:
        value = criterion.get(field)
        if not value or not str(value).strip():
            issues.append(Issue(
                name, "error",
                f"acceptance[{cid}]: pattern={pattern} requer '{field}' "
                f"não-vazio",
            ))

    return issues


def validate_feature(path: Path) -> tuple[dict, list[Issue]]:
    issues: list[Issue] = []
    name = path.name
    if not FEATURE_FILE_RE.match(name):
        issues.append(Issue(name, "error", "nome inválido (esperado F-NNNN-slug.md)"))
    try:
        fm, _ = parse_frontmatter(path)
    except ValueError as e:
        return {}, [Issue(name, "error", str(e))]

    required = ["id", "name", "status", "user_value", "contracts", "acceptance"]
    for key in required:
        if key not in fm:
            issues.append(Issue(name, "error", f"campo ausente: {key}"))

    status = fm.get("status")
    if status and status not in VALID_FEATURE_STATUS:
        issues.append(Issue(name, "error", f"status inválido: {status}"))

    contracts = fm.get("contracts") or {}
    for p in _collect_contract_paths(contracts):
        file_part = p.split("::")[0]
        if not (ROOT / file_part).exists():
            issues.append(Issue(name, "warning", f"drift: caminho inexistente: {p}"))

    acceptance = fm.get("acceptance") or []
    if not isinstance(acceptance, list):
        issues.append(Issue(name, "error", "acceptance deve ser uma lista"))
    else:
        for idx, criterion in enumerate(acceptance):
            if not isinstance(criterion, dict):
                issues.append(Issue(
                    name, "error",
                    f"acceptance[#{idx}]: deve ser um objeto (mapping)",
                ))
                continue
            issues.extend(validate_ears_criterion(name, idx, criterion))

    return fm, issues


def validate_state_crosscheck(state_fm: dict,
                              features: list[dict],
                              decisions: list[dict]) -> list[Issue]:
    """Verifica que cada ID em active_features/active_decisions existe.

    Não detecta drift de contracts (isso é responsabilidade de
    `validate_feature`); aqui o foco é "memória mentirosa" — STATE.md
    citando IDs que não têm arquivo correspondente. ADR-0014.

    `features` deve ser a lista combinada de features ativas e
    arquivadas (run_audit faz a união antes de chamar). Cobertura
    histórica completa por F-0012.
    """
    issues: list[Issue] = []
    feature_ids = {f.get("id") for f in features if f.get("id")}
    decision_ids = {d.get("id") for d in decisions if d.get("id")}

    for fid in state_fm.get("active_features") or []:
        if fid not in feature_ids:
            issues.append(Issue(
                "STATE.md", "error",
                f"active_features cita {fid} mas nenhum arquivo "
                f"F-NNNN-*.md existe em manifest/features/ ou archive/",
            ))

    for did in state_fm.get("active_decisions") or []:
        if did not in decision_ids:
            issues.append(Issue(
                "STATE.md", "error",
                f"active_decisions cita {did} mas nenhum arquivo "
                f"NNNN-*.md existe em decisions/",
            ))

    return issues


# Paths considerados "código" para staleness check. Tudo que NÃO tem
# um destes prefixos / não é um destes nomes exatos é tratado como
# código (ADR-0014). Lista deliberadamente conservadora.
STALENESS_NONCODE_PREFIXES = (".agent-memory/", "tests/", "docs/")
STALENESS_NONCODE_EXACT = {
    "README.md", "CHANGELOG.md", "METHODOLOGY.md",
    "USER_GUIDE.md", "FUTURE_IMPROVEMENTS.md", "LICENSE",
    ".gitignore", ".gitattributes",
}


def _is_code_path(path: str) -> bool:
    p = path.replace("\\", "/")
    if p in STALENESS_NONCODE_EXACT:
        return False
    return not any(p.startswith(prefix) for prefix in STALENESS_NONCODE_PREFIXES)


def validate_state_freshness(root: Path, days: int = 7) -> list[Issue]:
    """Detecta sessões que tocaram código sem atualizar STATE.md.

    Opt-in via `agent-memory audit --check-staleness[=N]`. Heurística
    descrita em ADR-0014. Fail-soft: sem git ou sem commits no período,
    retorna lista vazia (não promove ausência de histórico a sinal).
    """
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={days} days ago",
             "--name-only", "--pretty=format:"],
            text=True, stderr=subprocess.DEVNULL, cwd=root,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    touched = {line.strip() for line in out.splitlines() if line.strip()}
    if not touched:
        return []

    state_relpath = ".agent-memory/STATE.md"
    state_was_touched = any(
        p.replace("\\", "/") == state_relpath for p in touched
    )
    if state_was_touched:
        return []

    code_files = [p for p in touched if _is_code_path(p)]
    if not code_files:
        return []

    return [Issue(
        "STATE.md", "warning",
        f"sem update há {days}+ dia(s) enquanto código foi commitado "
        f"({len(code_files)} arquivo(s) tocado(s) — ex: "
        f"{sorted(code_files)[0]}); considere /memory-debrief",
    )]


def validate_decision(path: Path) -> tuple[dict, list[Issue]]:
    issues: list[Issue] = []
    name = path.name
    if not DECISION_FILE_RE.match(name):
        issues.append(Issue(name, "error", "nome inválido (esperado NNNN-slug.md)"))
    try:
        fm, _ = parse_frontmatter(path)
    except ValueError as e:
        return {}, [Issue(name, "error", str(e))]

    for key in ("id", "date", "status"):
        if key not in fm:
            issues.append(Issue(name, "error", f"campo ausente: {key}"))

    status = fm.get("status")
    if status and status not in VALID_DECISION_STATUS:
        issues.append(Issue(name, "error", f"status inválido: {status}"))

    return fm, issues


# --- collision detection (pre-merge) ---------------------------------------

def get_id_to_file_map(ref: str, subdir: str) -> dict[str, str]:
    """Mapeia IDs para nomes de arquivos num ref Git."""
    import subprocess
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", ref, subdir],
            text=True, stderr=subprocess.DEVNULL, cwd=ROOT,
        )
    except subprocess.CalledProcessError:
        return {}

    mapping: dict[str, str] = {}
    for line in out.splitlines():
        name = Path(line).name
        if subdir == ".agent-memory/manifest/features":
            m = re.match(r"^(F-\d{4})-", name)
            if m:
                mapping[m.group(1)] = name
        elif subdir == ".agent-memory/decisions":
            m = re.match(r"^(\d{4})-", name)
            if m:
                mapping[f"ADR-{m.group(1)}"] = name
    return mapping


def check_collisions(base_ref: str) -> list[Issue]:
    """Detecta colisões de IDs entre HEAD atual e o base_ref.

    Uma colisão ocorre quando o mesmo ID aparece em ambas as branches
    apontando para arquivos com nomes diferentes — sinal de que duas
    branches paralelas criaram artefatos com o mesmo ID. O merge
    produzirá estado semanticamente quebrado.
    """
    issues: list[Issue] = []

    base_features = get_id_to_file_map(base_ref, ".agent-memory/manifest/features")
    head_features = get_id_to_file_map("HEAD", ".agent-memory/manifest/features")
    for fid, head_name in sorted(head_features.items()):
        base_name = base_features.get(fid)
        if base_name and base_name != head_name:
            issues.append(Issue(
                "manifest", "error",
                f"colisão de ID com {base_ref}: {fid} aponta para "
                f"'{head_name}' aqui e '{base_name}' lá "
                f"(renumere antes do merge)",
            ))

    base_adrs = get_id_to_file_map(base_ref, ".agent-memory/decisions")
    head_adrs = get_id_to_file_map("HEAD", ".agent-memory/decisions")
    for aid, head_name in sorted(head_adrs.items()):
        base_name = base_adrs.get(aid)
        if base_name and base_name != head_name:
            issues.append(Issue(
                "decisions", "error",
                f"colisão de ID com {base_ref}: {aid} aponta para "
                f"'{head_name}' aqui e '{base_name}' lá "
                f"(renumere antes do merge)",
            ))

    return issues


# --- index generation ------------------------------------------------------

def gen_manifest_index(features: list[dict]) -> str:
    rows = [
        "# Índice de features", "",
        "| ID | Nome | Status | Versão | ADRs | Depende |",
        "|---|---|---|---|---|---|",
    ]
    for f in sorted(features, key=lambda x: str(x.get("id", ""))):
        rows.append(
            f"| {f.get('id', '?')} "
            f"| {f.get('name', '?')} "
            f"| {f.get('status', '?')} "
            f"| {f.get('version', '—')} "
            f"| {','.join(f.get('decisions') or []) or '—'} "
            f"| {','.join(f.get('depends_on') or []) or '—'} |"
        )
    rows += [
        "",
        f"_Gerado por `agent-memory audit` em "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}. "
        f"Não edite manualmente._",
    ]
    return "\n".join(rows) + "\n"


def gen_archive_index(features: list[dict]) -> str:
    """Mesma estrutura de gen_manifest_index, mas para features arquivadas.

    Existência separada (em manifest/archive/INDEX.md) reduz o tamanho
    do INDEX principal carregado por `memory-bootstrap`. F-0012, ADR-0015.
    """
    rows = [
        "# Índice de features arquivadas", "",
        "Features `shipped` e fora de `STATE.md::active_features` movidas",
        "por `agent-memory archive --apply`. IDs continuam resolvíveis pelo",
        "cross-check; mantenha aqui o registro histórico, sem onerar o INDEX",
        "principal.", "",
        "| ID | Nome | Status | Versão | ADRs | Depende |",
        "|---|---|---|---|---|---|",
    ]
    for f in sorted(features, key=lambda x: str(x.get("id", ""))):
        rows.append(
            f"| {f.get('id', '?')} "
            f"| {f.get('name', '?')} "
            f"| {f.get('status', '?')} "
            f"| {f.get('version', '—')} "
            f"| {','.join(f.get('decisions') or []) or '—'} "
            f"| {','.join(f.get('depends_on') or []) or '—'} |"
        )
    rows += [
        "",
        f"_Gerado por `agent-memory audit` em "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}. "
        f"Não edite manualmente._",
    ]
    return "\n".join(rows) + "\n"


def gen_decisions_index(decisions: list[dict]) -> str:
    rows = [
        "# Índice de decisões", "",
        "| ID | Data | Status | Tags | Afeta |",
        "|---|---|---|---|---|",
    ]
    for d in sorted(decisions, key=lambda x: str(x.get("id", ""))):
        rows.append(
            f"| {d.get('id', '?')} "
            f"| {d.get('date', '?')} "
            f"| {d.get('status', '?')} "
            f"| {','.join(d.get('tags') or []) or '—'} "
            f"| {','.join(d.get('affects_features') or []) or '—'} |"
        )
    rows += [
        "",
        f"_Gerado por `agent-memory audit` em "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}. "
        f"Não edite manualmente._",
    ]
    return "\n".join(rows) + "\n"


# --- metrics ---------------------------------------------------------------

def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def compute_metrics(state_fm: dict, features: list[dict],
                    decisions: list[dict], issues: list[Issue]) -> dict:
    errors = sum(1 for i in issues if i.severity == "error")

    # Custo de retomada conta o que o agente carrega no bootstrap.
    # AGENT.md é canônica; CLAUDE.md, se existir, é redirect mínimo
    # mas inclusa porque o Claude Code carrega ambos.
    cost = 0
    for p in (AGENT, CLAUDE, STATE,
              MANIFEST_DIR / "INDEX.md",
              DECISIONS_DIR / "INDEX.md"):
        if p.exists():
            cost += p.stat().st_size

    freshness = None
    updated = _parse_dt(state_fm.get("updated_at"))
    if updated:
        delta = datetime.now(timezone.utc) - updated
        freshness = round(delta.total_seconds() / 3600, 1)

    with_tests = 0
    for f in features:
        tests = (f.get("contracts") or {}).get("tests")
        if not tests:
            continue
        paths = tests if isinstance(tests, list) else [tests]
        if all((ROOT / str(p).split("::")[0]).exists() for p in paths):
            with_tests += 1
    coverage = round(with_tests / len(features), 2) if features else 1.0

    drift = [i.message for i in issues if i.message.startswith("drift:")]

    now = datetime.now(timezone.utc)
    shipped_30d = 0
    in_progress = 0
    deprecated_referenced = 0
    deprecated_ids = {f.get("id") for f in features
                      if f.get("status") == "deprecated"}

    for f in features:
        if f.get("status") == "shipped":
            intro = _parse_dt(f.get("introduced"))
            if intro and (now - intro).days <= 30:
                shipped_30d += 1
        elif f.get("status") == "in_progress":
            in_progress += 1
        for dep in f.get("depends_on") or []:
            if dep in deprecated_ids and f.get("status") != "deprecated":
                deprecated_referenced += 1

    accepted = sum(1 for d in decisions if d.get("status") == "accepted")
    superseded = sum(1 for d in decisions if d.get("status") == "superseded")
    super_ratio = round(superseded / len(decisions), 2) if decisions else 0.0

    stale = 0
    for d in decisions:
        if d.get("status") != "accepted":
            continue
        date = _parse_dt(d.get("date"))
        if date and (now - date).days > 180:
            stale += 1

    return {
        "schema_compliance": 1.0 if errors == 0 else 0.0,
        "resumption_cost_bytes": cost,
        "state_freshness_hours": freshness,
        "manifest_coverage": coverage,
        "manifest_drift": drift,
        "manifest_velocity": {
            "shipped_last_30d": shipped_30d,
            "in_progress_open": in_progress,
            "deprecated_still_referenced": deprecated_referenced,
        },
        "decision_health": {
            "accepted": accepted,
            "superseded": superseded,
            "supersession_ratio": super_ratio,
            "stale_over_180d": stale,
        },
        "violations_count": errors,
    }


# --- entry points ----------------------------------------------------------

def run_audit(write_indices: bool = True,
              check_collisions_against: str | None = None,
              check_staleness_days: int | None = None) -> dict:
    all_issues: list[Issue] = []

    agent_fm, issues = validate_agent(AGENT)
    all_issues.extend(issues)

    max_state = (agent_fm.get("budgets") or {}).get(
        "state_max_bytes", DEFAULT_STATE_BUDGET
    )
    state_fm, issues = validate_state(STATE, max_state)
    all_issues.extend(issues)

    features: list[dict] = []
    if FEATURES_DIR.exists():
        for fp in sorted(FEATURES_DIR.glob("F-*.md")):
            fm, issues = validate_feature(fp)
            all_issues.extend(issues)
            if fm:
                features.append(fm)

    # Features arquivadas (F-0012, ADR-0015) — mesma validação de schema
    # e drift, mas índice separado em manifest/archive/INDEX.md.
    archived_features: list[dict] = []
    if ARCHIVE_DIR.exists():
        for fp in sorted(ARCHIVE_DIR.glob("F-*.md")):
            fm, issues = validate_feature(fp)
            all_issues.extend(issues)
            if fm:
                archived_features.append(fm)

    decisions: list[dict] = []
    if DECISIONS_DIR.exists():
        for dp in sorted(DECISIONS_DIR.glob("[0-9]*.md")):
            if dp.parent != DECISIONS_DIR:
                continue
            fm, issues = validate_decision(dp)
            all_issues.extend(issues)
            if fm:
                decisions.append(fm)

    all_features = features + archived_features

    # Cross-check de IDs ativos contra arquivos existentes (ADR-0014).
    # Roda por default; falhas viram errors e bloqueiam o pre-commit hook.
    all_issues.extend(validate_state_crosscheck(state_fm, all_features, decisions))

    # Detecção de colisões pré-merge (opcional)
    if check_collisions_against:
        all_issues.extend(check_collisions(check_collisions_against))

    # Staleness check (opt-in via --check-staleness; ADR-0014).
    if check_staleness_days is not None:
        all_issues.extend(validate_state_freshness(ROOT, check_staleness_days))

    if write_indices:
        if MANIFEST_DIR.exists():
            (MANIFEST_DIR / "INDEX.md").write_text(
                gen_manifest_index(features), encoding="utf-8"
            )
            if archived_features:
                ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
                (ARCHIVE_DIR / "INDEX.md").write_text(
                    gen_archive_index(archived_features), encoding="utf-8"
                )
        if DECISIONS_DIR.exists():
            (DECISIONS_DIR / "INDEX.md").write_text(
                gen_decisions_index(decisions), encoding="utf-8"
            )

    metrics = compute_metrics(state_fm, all_features, decisions, all_issues)
    return {
        "metrics": metrics,
        "issues": [asdict(i) for i in all_issues],
    }


def print_report(result: dict) -> None:
    m = result["metrics"]
    print("=" * 60)
    print("Relatório de auditoria")
    print("=" * 60)
    print(f"Project root:              {ROOT}")
    print(f"Conformidade de schema:    {m['schema_compliance']:.2f}")
    print(f"Custo de retomada:         {m['resumption_cost_bytes']:,} bytes")
    fresh = m["state_freshness_hours"]
    fresh_str = f"{fresh} h" if fresh is not None else "—"
    print(f"Frescor de estado:         {fresh_str}")
    print(f"Cobertura do manifest:     {m['manifest_coverage']:.0%}")
    print(f"Drift detectado:           {len(m['manifest_drift'])} casos")
    print()
    v = m["manifest_velocity"]
    print("Velocity:")
    print(f"  shipped (30d):           {v['shipped_last_30d']}")
    print(f"  em progresso:            {v['in_progress_open']}")
    print(f"  refs a deprecated:       {v['deprecated_still_referenced']}")
    print()
    h = m["decision_health"]
    print("Saúde de decisões:")
    print(f"  accepted:                {h['accepted']}")
    print(f"  superseded:              {h['superseded']} "
          f"(ratio {h['supersession_ratio']})")
    print(f"  > 180 dias sem revisão:  {h['stale_over_180d']}")
    print()

    issues = result["issues"]
    if issues:
        print(f"Issues encontrados: {len(issues)}")
        for i in issues:
            print(f"  [{i['severity']}] {i['artifact']}: {i['message']}")
    else:
        print("Nenhum issue encontrado.")


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "audit",
        help="Valida artefatos da metodologia e regenera índices",
    )
    p.add_argument("--json", action="store_true",
                   help="output em JSON")
    p.add_argument("--no-index", action="store_true",
                   help="não regenerar índices")
    p.add_argument("--strict", action="store_true",
                   help="trata warnings (drift) como errors")
    p.add_argument("--check-collisions", metavar="REF",
                   help="detecta colisões de IDs contra REF "
                   "(ex: origin/main) antes de merge")
    p.add_argument("--check-staleness", nargs="?", const=7, type=int,
                   metavar="DAYS",
                   help="warning se commits dos últimos N dias (default 7) "
                   "tocaram código sem atualizar STATE.md (ADR-0014)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    _init_paths()

    result = run_audit(
        write_indices=not args.no_index,
        check_collisions_against=args.check_collisions,
        check_staleness_days=args.check_staleness,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_report(result)

    issues = result["issues"]
    errors = sum(1 for i in issues if i["severity"] == "error")
    if args.strict:
        warnings = sum(1 for i in issues if i["severity"] == "warning")
        if warnings:
            print(f"\n[strict] {warnings} warning(s) promovidos a error.",
                  file=sys.stderr)
            errors += warnings
    return 1 if errors else 0
