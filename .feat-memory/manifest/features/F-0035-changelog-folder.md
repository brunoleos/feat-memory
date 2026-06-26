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
  - {id: A1, pattern: event, trigger: "feat-memory release é invocado", response: "congela UNRELEASED.md em changelog/<VERSION>.md (VERSION atual, sem bump — ADR-0045), reinicia o UNRELEASED, regenera INDEX.md, commita e cria a tag v<VERSION>"}
  - {id: A2, pattern: ubiquitous, requirement: "cada changelog/<tag>.md é imutável após o release"}
  - {id: A3, pattern: optional, feature: "--no-commit/--no-tag", response: "deixa as mutações staged para revisão humana antes de fechar"}
depends_on: []
decisions: [ADR-0042, ADR-0045]
---
