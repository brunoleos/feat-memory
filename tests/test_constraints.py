"""Testes dos checkers declarativos de constraint (F-0024, ADR-0028)."""

from __future__ import annotations

from pathlib import Path

from feat_memory.governance import constraints
from feat_memory.governance import audit


# --- forbid_paths ----------------------------------------------------------


def test_forbid_paths_flags_matching_file(tmp_path: Path):
    (tmp_path / "deploy.sh").write_text("echo hi", encoding="utf-8")
    out = constraints._check_forbid_paths(
        {"type": "forbid_paths", "globs": ["**/*.sh"]}, tmp_path)
    assert len(out) == 1
    assert "deploy.sh" in out[0]


def test_forbid_paths_clean_when_no_match(tmp_path: Path):
    (tmp_path / "main.py").write_text("x = 1", encoding="utf-8")
    out = constraints._check_forbid_paths(
        {"globs": ["**/*.sh", "**/*.bash"]}, tmp_path)
    assert out == []


def test_forbid_paths_skips_excluded_dirs(tmp_path: Path):
    """Arquivos sob .git/ etc. não contam."""
    git = tmp_path / ".git" / "hooks"
    git.mkdir(parents=True)
    (git / "pre-commit.sh").write_text("x", encoding="utf-8")
    out = constraints._check_forbid_paths({"globs": ["**/*.sh"]}, tmp_path)
    assert out == []


def test_forbid_paths_respects_exclude(tmp_path: Path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "ok.sh").write_text("x", encoding="utf-8")
    out = constraints._check_forbid_paths(
        {"globs": ["**/*.sh"], "exclude": ["scripts/*"]}, tmp_path)
    assert out == []


# --- require_paths ---------------------------------------------------------


def test_require_paths_flags_absence(tmp_path: Path):
    out = constraints._check_require_paths({"globs": ["LICENSE"]}, tmp_path)
    assert len(out) == 1


def test_require_paths_ok_when_present(tmp_path: Path):
    (tmp_path / "LICENSE").write_text("MIT", encoding="utf-8")
    assert constraints._check_require_paths({"globs": ["LICENSE"]}, tmp_path) == []


# --- forbid_pattern / require_pattern --------------------------------------


def test_forbid_pattern_flags_match(tmp_path: Path):
    (tmp_path / "t.md").write_text("usa a versão 1.2.3 hardcoded", encoding="utf-8")
    out = constraints._check_forbid_pattern(
        {"globs": ["**/*.md"], "pattern": r"\d+\.\d+\.\d+"}, tmp_path)
    assert len(out) == 1
    assert "t.md" in out[0]


def test_require_pattern_flags_missing(tmp_path: Path):
    (tmp_path / "a.py").write_text("print(1)", encoding="utf-8")
    out = constraints._check_require_pattern(
        {"globs": ["**/*.py"], "pattern": r"# SPDX-License"}, tmp_path)
    assert len(out) == 1


# --- dependencies ----------------------------------------------------------


def test_dependencies_pyproject_allow_pass(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["pyyaml>=6.0"]\n', encoding="utf-8")
    out = constraints._check_dependencies(
        {"manifest": "pyproject.toml", "allow": ["pyyaml"]}, tmp_path)
    assert out == []


def test_dependencies_pyproject_allow_flags_extra(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["pyyaml", "requests>=2"]\n',
        encoding="utf-8")
    out = constraints._check_dependencies(
        {"manifest": "pyproject.toml", "allow": ["pyyaml"]}, tmp_path)
    assert len(out) == 1
    assert "requests" in out[0]


def test_dependencies_ignores_optional_deps(tmp_path: Path):
    """Só [project].dependencies entra; dev/optional ficam fora."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["pyyaml"]\n'
        '[project.optional-dependencies]\ndev = ["pytest>=7"]\n', encoding="utf-8")
    out = constraints._check_dependencies(
        {"manifest": "pyproject.toml", "allow": ["pyyaml"]}, tmp_path)
    assert out == []


def test_dependencies_requirements_txt(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text(
        "# comment\npyyaml==6.0\nrequests\n", encoding="utf-8")
    out = constraints._check_dependencies(
        {"manifest": "requirements.txt", "forbid": ["requests"]}, tmp_path)
    assert len(out) == 1
    assert "requests" in out[0]


def test_dependencies_package_json(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"left-pad": "1.0.0"}}', encoding="utf-8")
    out = constraints._check_dependencies(
        {"manifest": "package.json", "allow": ["react"]}, tmp_path)
    assert len(out) == 1
    assert "left-pad" in out[0]


def test_dependencies_missing_manifest(tmp_path: Path):
    out = constraints._check_dependencies(
        {"manifest": "pyproject.toml", "allow": ["pyyaml"]}, tmp_path)
    assert len(out) == 1
    assert "não encontrado" in out[0]


# --- shape validation ------------------------------------------------------


def test_validate_check_shape_ok():
    assert constraints.validate_check_shape(
        {"type": "forbid_paths", "globs": ["*.sh"]}) == []


def test_validate_check_shape_unknown_type():
    problems = constraints.validate_check_shape({"type": "nope"})
    assert problems and "desconhecido" in problems[0]


def test_validate_check_shape_missing_param():
    problems = constraints.validate_check_shape({"type": "forbid_pattern", "globs": ["*"]})
    assert any("pattern" in p for p in problems)


def test_validate_check_shape_bad_regex():
    problems = constraints.validate_check_shape(
        {"type": "forbid_pattern", "globs": ["*"], "pattern": "("})
    assert any("regex" in p for p in problems)


def test_validate_check_shape_dependencies_needs_allow_or_forbid():
    problems = constraints.validate_check_shape(
        {"type": "dependencies", "manifest": "pyproject.toml"})
    assert any("allow" in p for p in problems)


# --- check_constraints (runner + severity) ---------------------------------


def test_check_constraints_hard_violation_is_error(tmp_path: Path):
    (tmp_path / "x.sh").write_text("x", encoding="utf-8")
    fm = {"constraints": [
        {"id": "C1", "severity": "hard",
         "check": {"type": "forbid_paths", "globs": ["**/*.sh"]}},
    ]}
    res = constraints.check_constraints(fm, tmp_path)
    assert res["checked"] == 1
    assert res["violations"] == 1
    assert res["issues"][0].severity == "error"
    assert "C1" in res["issues"][0].message


def test_check_constraints_soft_violation_is_warning(tmp_path: Path):
    (tmp_path / "x.sh").write_text("x", encoding="utf-8")
    fm = {"constraints": [
        {"id": "C9", "severity": "soft",
         "check": {"type": "forbid_paths", "globs": ["**/*.sh"]}},
    ]}
    res = constraints.check_constraints(fm, tmp_path)
    assert res["issues"][0].severity == "warning"


def test_check_constraints_without_check_is_declarative(tmp_path: Path):
    """Constraint sem `check` não gera Issue (back-compat)."""
    fm = {"constraints": [{"id": "C3", "severity": "hard", "rule": "prosa"}]}
    res = constraints.check_constraints(fm, tmp_path)
    assert res == {"issues": [], "checked": 0, "violations": 0}


def test_check_constraints_malformed_is_schema_error(tmp_path: Path):
    fm = {"constraints": [
        {"id": "C1", "severity": "hard", "check": {"type": "bogus"}},
    ]}
    res = constraints.check_constraints(fm, tmp_path)
    assert res["checked"] == 0
    assert res["issues"][0].severity == "error"
    assert "inválido" in res["issues"][0].message


# --- integração end-to-end via run_audit -----------------------------------


def _write_min_state(state: Path) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        "---\nschema_version: 2\nupdated_at: 2026-06-03T00:00:00Z\n"
        "active_features: []\n---\n", encoding="utf-8")


def test_run_audit_blocks_on_hard_violation(audit_with_tmp_root):
    """Uma constraint hard com check violado vira error no relatório do audit."""
    root = audit_with_tmp_root
    root.joinpath("AGENTS.md").write_text(
        "---\nschema_version: 2\nproject: x\n"
        "constraints:\n"
        "  - id: C1\n    severity: hard\n"
        "    check: {type: forbid_paths, globs: ['**/*.sh']}\n"
        "references: {}\nbudgets: {}\n---\n", encoding="utf-8")
    _write_min_state(root / ".feat-memory" / "STATE.md")
    (root / "bad.sh").write_text("echo", encoding="utf-8")

    result = audit.run_audit(write_indices=False)
    errs = [i for i in result["issues"]
            if i["severity"] == "error" and "C1" in i["message"]]
    assert len(errs) == 1
    cc = result["metrics"]["constraint_conformance"]
    assert cc["checked"] == 1 and cc["violations"] == 1 and cc["pass"] is False


def test_run_audit_clean_when_constraints_satisfied(audit_with_tmp_root):
    root = audit_with_tmp_root
    root.joinpath("AGENTS.md").write_text(
        "---\nschema_version: 2\nproject: x\n"
        "constraints:\n"
        "  - id: C1\n    severity: hard\n"
        "    check: {type: forbid_paths, globs: ['**/*.sh']}\n"
        "references: {}\nbudgets: {}\n---\n", encoding="utf-8")
    _write_min_state(root / ".feat-memory" / "STATE.md")

    result = audit.run_audit(write_indices=False)
    cc = result["metrics"]["constraint_conformance"]
    assert cc["checked"] == 1 and cc["pass"] is True
