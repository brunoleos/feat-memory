---
id: F-0026
name: code-first-genesis
status: shipped
introduced: 2026-06-03
version: 0.13.0
user_value: >
  A gênese retroativa de projetos legados vira engenharia reversa multi-fonte
  code-first: a skill triangula testes (spec executável do uso), telas (mapa de
  capacidades visíveis), documentação, código e dependências para extrair
  capacidades (→ features) e decisões (→ ADRs), com o git apenas datando/
  justificando. O `feat-memory migrate` detecta testes, UI e entrypoints de
  forma agnóstica de linguagem, então projetos JS/TS/Go/etc. recebem pistas
  ricas em vez de zero.
contracts:
  api:
    - src/feat_memory/memory/migrate.py::detect_entry_points
    - src/feat_memory/memory/migrate.py::detect_test_signals
    - src/feat_memory/memory/migrate.py::detect_ui_signals
    - src/feat_memory/memory/migrate.py::run
  data:
    - src/feat_memory/data/skills/memory-deploy/SKILL.md
  tests:
    - tests/test_migrate.py
acceptance:
  - {id: A1, pattern: ubiquitous, requirement: "a skill memory-deploy conduz a Etapa 3 como engenharia reversa multi-fonte: triangula testes, telas, docs, código e deps antes de consultar o git, que é secundário"}
  - {id: A2, pattern: event, trigger: "`migrate` varre um projeto com diretórios de entrypoint (routes/, cli/, api/, …) em qualquer linguagem reconhecida", response: "lista esses diretórios com a contagem de arquivos de fonte, podando vendored/build"}
  - {id: A3, pattern: unwanted, trigger: "arquivos vivem em node_modules/dist/.venv", response: "não entram em nenhuma contagem (entrypoints, testes ou UI)"}
  - {id: A4, pattern: event, trigger: "`migrate` encontra testes (dir de convenção ou arquivos test_*/*.spec) ou camada de UI (views/pages ou arquivos .vue/.jsx/.tsx/…)", response: "reporta-os como sinais [1] e [2], antes dos entrypoints e do git, na ordem de precisão"}
  - {id: A5, pattern: state, state: "o git log não tem padrões de decisão (histórico squashado)", response: "`migrate` reporta isso como esperado, não bloqueio, e a gênese segue pelas fontes primárias"}
  - {id: A6, pattern: ubiquitous, requirement: "o output do migrate apresenta as fontes na ordem de precisão (testes → UI → entrypoints → git), rotuladas, e o JSON inclui test_signals/ui_signals"}
depends_on: []
decisions: [ADR-0030, ADR-0031]
---

# F-0026 · code-first-genesis

Inverte a ordem da gênese retroativa (ADR-0030) e a aprofunda num protocolo de
engenharia reversa multi-fonte (ADR-0031). Motivado pela adoção em `tensegrams`,
onde o histórico squashado rendia quase nada e o `detect_entry_points` Python-só
retornava vazio num projeto JS. A skill `memory-deploy` ganha uma Etapa 3 que ranqueia
as fontes por precisão (testes → telas → docs → código → deps → git) e codifica
técnicas anti-alucinação (triangulação, confiança em camadas, cobertura como mapa de
importância). O `migrate` passa a emitir sinais de teste (`detect_test_signals`) e UI
(`detect_ui_signals`) além de entrypoints, todos agnósticos de linguagem via `os.walk`
com poda de vendored/build, e reordena o output para a ordem de precisão. `acceptance`
das features passa a derivar das asserções dos testes quando existem.
