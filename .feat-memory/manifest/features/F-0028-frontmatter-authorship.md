---
id: F-0028
name: frontmatter-authorship
status: shipped
introduced: 2026-06-04
version: 0.14.0
user_value: >
  A adoção legacy não trava mais numa contradição: a skill memory-deploy propõe
  o frontmatter da AGENTS.md (project, stack e constraints rascunhadas do
  código/tooling/deps) a partir de evidência e apresenta ao mantenedor para
  aprovação — nunca cristaliza valores sem aval. Skill, comentário injetado no
  esqueleto e descrição no bloco passam a dizer a mesma regra.
contracts:
  api:
    - src/feat_memory/data/skills/memory-deploy/SKILL.md
    - src/feat_memory/data/templates/AGENTS.frontmatter-skeleton.md
    - src/feat_memory/data/templates/AGENTS.md
acceptance:
  - {id: A1, pattern: ubiquitous, requirement: "a skill memory-deploy propõe project/stack/constraints a partir de evidência observável e apresenta para aprovação humana antes de gravar"}
  - {id: A2, pattern: unwanted, trigger: "o agente gravaria valores de frontmatter não-aprovados como se fossem decisão oficial", response: "é proibido — equivale a cristalização silenciosa de ADR; o gate é aprovação humana"}
  - {id: A3, pattern: ubiquitous, requirement: "a SKILL, o comentário injetado no esqueleto de frontmatter e a descrição da skill no bloco da AGENTS.md expressam a mesma regra (propõe a partir de evidência, humano aprova) — sem contradição"}
depends_on: [F-0025]
decisions: [ADR-0032]
---

# F-0028 · frontmatter-authorship

Resolve a contradição nº2 do relatório: a SKILL proibia escrever na AGENTS.md enquanto o
comentário injetado (ADR-0029) mandava preencher. ADR-0032 reconcilia: o agente propõe o
frontmatter inteiro a partir de evidência (project = nome do dir; stack = manifestos;
constraints = tooling/CI/deps/lições) e apresenta para aprovação; o gate é aprovação, não
proibição. Os três artefatos que o agente lê — SKILL, comentário do esqueleto e descrição
no bloco — foram alinhados para dizer a mesma coisa.
