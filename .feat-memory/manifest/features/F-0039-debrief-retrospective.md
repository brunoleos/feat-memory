---
id: F-0039
name: debrief-retrospective
status: shipped
introduced: 2026-06-26
version: 2.1.0
user_value: Ao fechar a sessão, a debrief reflete inline (escopo, bugs, achados, resumo honesto) e tria ideias do futuro para o funil (ideas.md) com ask-before-register, sem persistir narrativa.
contracts:
  api: src/feat_memory/data/skills/memory-debrief/SKILL.md
  tests: tests/test_skills_methodology.py
acceptance:
  - {id: A1, pattern: event, trigger: "memory-debrief ao fechar sessão", response: "produz retrospectiva inline e roteia saídas duráveis (release→UNRELEASED, decisão→ADR, capacidade→Feature)"}
  - {id: A2, pattern: event, trigger: "uma ideia do futuro surge na sessão", response: "tria pelo tipo e pergunta ao usuário (resolver agora / adiar para ideas.md / descartar) antes de registrar; na dúvida devolve a bifurcação"}
  - {id: A3, pattern: unwanted, trigger: "tentação de persistir a narrativa da retrospectiva", response: "não persiste — só ideias acionáveis vão para o ideas.md"}
depends_on: [F-0038]
decisions: [ADR-0048]
---
