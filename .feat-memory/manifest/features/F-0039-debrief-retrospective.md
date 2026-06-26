---
id: F-0039
name: debrief-retrospective
status: shipped
introduced: 2026-06-26
version: 2.1.0
user_value: Ao fechar a sessão, a debrief reflete inline (escopo, bugs, achados, resumo honesto) e captura propostas de evolução no backlog com ask-before-register, sem persistir narrativa.
contracts:
  api: src/feat_memory/data/skills/memory-debrief/SKILL.md
  tests: tests/test_skills_methodology.py
acceptance:
  - {id: A1, pattern: event, trigger: "memory-debrief ao fechar sessão", response: "produz retrospectiva inline e roteia saídas duráveis (release→UNRELEASED, decisão→ADR, capacidade→Feature)"}
  - {id: A2, pattern: event, trigger: "uma proposta de evolução do sistema surge na sessão", response: "pergunta ao usuário (resolver agora / adiar / descartar) antes de registrar em suggestions.md"}
  - {id: A3, pattern: unwanted, trigger: "tentação de persistir a narrativa da retrospectiva", response: "não persiste — só pendências acionáveis vão para o backlog"}
depends_on: [F-0038]
decisions: [ADR-0046]
---
