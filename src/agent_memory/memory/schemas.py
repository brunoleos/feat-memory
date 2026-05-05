"""schemas.py — Validação de schema dos quatro artefatos da metodologia.

`validate_agent`, `validate_state`, `validate_feature`, `validate_decision`
recebem um path e retornam (frontmatter, list[Issue]). Schemas seguem
ADR-0002 (constraints hard/soft) e ADR-0003 (acceptance EARS).

`Issue` é o tipo de violação compartilhado com `governance.audit` (que
adiciona métricas, drift e cross-check sobre essa base).

Parte de `memory/`. Importa apenas de `shared/`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from agent_memory.shared.parsing import parse_frontmatter
from agent_memory.shared import paths as _paths


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
        if not (_paths.ROOT / file_part).exists():
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
