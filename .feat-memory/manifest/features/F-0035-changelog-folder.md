---
id: F-0035
name: changelog-folder
status: in_progress
introduced: 2026-06-26
version: 2.0.0
user_value: O histórico de releases vive como um arquivo imutável por tag em .feat-memory/changelog/, com INDEX gerado e um comando que congela cada release.
contracts:
  api: src/feat_memory/memory/changelog.py::run_release
  tests: tests/test_changelog.py
acceptance:
  - {id: A1, pattern: event, trigger: "feat-memory release X.Y.Z é invocado", response: "valida o bump SemVer, bumpa VERSION, congela UNRELEASED.md em changelog/X.Y.Z.md, cria UNRELEASED.md vazio, regenera INDEX.md e cria commit + tag vX.Y.Z"}
  - {id: A2, pattern: ubiquitous, requirement: "cada changelog/<tag>.md é imutável após o release"}
  - {id: A3, pattern: optional, feature: "--no-commit/--no-tag", response: "deixa as mutações staged para revisão humana antes de fechar"}
depends_on: []
decisions: [ADR-0042]
---
