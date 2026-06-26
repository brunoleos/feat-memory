---
id: F-0037
name: changelog-layout-migration
status: planned
introduced: 2026-06-26
version: 2.0.0
user_value: Um comando migra o layout legado (CHANGELOG.md monolítico + STATE.md + checkpoints/) para o novo (changelog/ + UNRELEASED.md), idempotente e não-destrutivo.
contracts:
  api: src/feat_memory/memory/changelog.py::migrate_to_changelog_folder
  tests: tests/test_changelog_migration.py
acceptance:
  - {id: A1, pattern: event, trigger: "feat-memory migrate --to=changelog é invocado num projeto legado", response: "faz split do CHANGELOG.md por versão em changelog/<v>.md, move [Unreleased]→UNRELEASED.md, semeia do STATE.md, remove checkpoints/ e os arquivos legados"}
  - {id: A2, pattern: ubiquitous, requirement: "a migração é idempotente — re-rodar num layout já migrado é no-op"}
  - {id: A3, pattern: unwanted, trigger: "já existe um changelog/ populado no destino", response: "aborta sem sobrescrever e avisa para reconciliação manual"}
depends_on: [F-0035, F-0036]
decisions: [ADR-0042, ADR-0043]
---
