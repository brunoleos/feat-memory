---
id: ADR-0028
date: 2026-06-03
status: accepted
version: 0.12.0
supersedes: null
superseded_by: null
affects_features: [F-0024]
related: [ADR-0002, ADR-0021, ADR-0024, ADR-0009]
tags: [constitution, constraints, governance, enforcement, sdd, dogfooding]
---

# ADR-0028 · constraints `hard` ganham checkers declarativos executáveis no audit

## Contexto

As restrições do projeto (`C1`..`C4` no frontmatter de `AGENTS.md`) são **prosa
livre** com `severity: hard|soft`. O `validate_agent` só confere que a chave
`constraints` existe; **nada checa se o código viola a restrição de fato**. A
constituição promete "hard bloqueia o build quando violada", mas na prática a
restrição é lida pelo agente, não imposta pela ferramenta. Uma constituição que é
só *declarada* deriva exatamente como o vibe-coding que a metodologia combate.

O posicionamento estratégico do `agent-memory` no ecossistema spec-driven
development (SDD) é ser **a melhor camada de "constitution"** — o substrato durável
e governado que os agentes referenciam toda sessão. Toda ferramenta SDND (Spec
Kit, Kiro, BMAD) tem uma constitution *fraca e não-verificada*. Tornar a
constituição **enforced** é o diferencial defensável dessa camada: uma constituição
*verificada a cada commit* é categoricamente superior a uma que é só lida.

O item "Linting de constraints hard" estava `[Adiado]` em FUTURE_IMPROVEMENTS, com
a razão: *"vago e caro de generalizar; cada regra exige um validador próprio"*.
Essa razão é o que esta decisão resolve — não com um validador por regra, mas com
um **conjunto fechado de checkers genéricos compostos via YAML**.

## Decisão

Cada constraint pode declarar um bloco `check` **opcional** no frontmatter. Sem
`check`, a constraint permanece puramente declarativa (back-compat total — o
comportamento atual). Com `check`, o `audit` executa o checker correspondente.

```yaml
- id: C1
  severity: hard
  rule: "Pure Python; sem shell scripts."
  check:
    type: forbid_paths
    globs: ["**/*.sh", "**/*.bash"]
```

1. **Conjunto FECHADO de cinco checkers genéricos** — `forbid_paths`,
   `require_paths`, `forbid_pattern`, `require_pattern`, `dependencies`. O projeto
   compõe restrições via YAML, **sem escrever Python**. O conjunto fechado é o
   antídoto à razão que adiou o item ("cada regra exige um validador"): a
   expressividade é deliberadamente limitada a globs, regex e manifestos de
   dependência, que cobrem a maioria das constraints mecanizáveis sem um motor de
   AST por linguagem.

2. **Vive em `governance/constraints.py`, não em `memory/schemas.py`.** Executar um
   checker exige varrer a árvore do repositório — isso é governança, não validação
   de schema. ADR-0021 proíbe `memory ⇒ governance`; logo a *execução* e a
   *validação de forma* do bloco `check` ficam em governance, que pode importar
   `memory.schemas.Issue`. O `run_audit` chama `check_constraints(agent_fm, ROOT)`
   logo após `validate_agent`.

3. **A violação herda a `severity` da constraint.** `hard` → `error` (bloqueia o
   build sempre, mais forte que drift, que só bloqueia sob `--strict`); `soft` →
   `warning`. Isso codifica a doutrina já escrita em `AGENTS.md` ("hard bloqueia,
   soft apenas warning"). Um `check` **malformado** (type desconhecido, param
   faltando, regex inválido) é `error` de schema — bloqueia como EARS malformado.

4. **Agnóstico de linguagem, stdlib + pyyaml apenas (C2 preservada).** Globs via
   `pathlib`, regex via `re`, manifestos via `tomllib`/`json`/parse de linha. O
   checker `dependencies` cobre genericamente `pyproject.toml`, `requirements.txt`
   e `package.json` — serve qualquer projeto consumidor, não só Python.

5. **Nem toda constraint é mecanizável, e o schema não finge que é.** `C3`
   ("segue a metodologia") e `C4` ("docs em pt-br") ficam **declarativas** — não há
   checker barato e confiável (detecção de idioma seria ruidosa ou exigiria
   dependência, ferindo C2). Enforça-se onde dá, declara-se onde não dá. Coerente
   com "cobertura zero é cobertura honesta".

6. **Dogfood (C3/ADR-0009).** `C1` e `C2` deste próprio repo ganham `check` na
   mesma entrega: `forbid_paths` sobre `*.sh`/`*.bash` e `dependencies` sobre
   `pyproject.toml` com `allow: [pyyaml]`. Ambos passam — o projeto que existe para
   impor constituição passa a ter a sua própria imposta.

## Consequências

Positivas: a constituição deixa de ser documento e vira lei executada; integra-se
de graça ao `--strict` do pre-commit e à CI; o dogfood prova C1/C2 por execução em
vez de afirmação; estabelece a categoria "constitution enforced" que diferencia o
projeto no SDD.

Negativas: checkers podem ter falso-positivo (mitigado por serem opt-in e pela
válvula `git commit --no-verify`, ADR-0008); o conjunto fechado limita a
expressividade (deliberado — evita o pântano de validadores por regra). C3/C4
seguem sem enforcement.

## Alternativas rejeitadas

- **Motor de lint genérico baseado em AST:** pesado e acoplado a linguagem — foi
  exatamente o que tornou o item de baixo ROI no roadmap. O conjunto fechado de
  checkers baseados em path/regex/dep dá 80% do valor sem isso.
- **Um validador Python por constraint:** o anti-padrão que esta ADR evita;
  transferiria custo de manutenção para cada projeto consumidor.
- **Validar a forma do `check` em `memory/schemas.py`:** violaria a direção de
  dependência de ADR-0021 (schemas precisaria conhecer os tipos de checker, que
  vivem em governance). Forma e execução ficam juntas em governance.
- **Violação `hard` como warning (só bloqueia sob --strict):** contradiz a doutrina
  escrita de que `hard` bloqueia o build. Mantida como `error`.
- **Heurística de idioma para enforçar C4:** ruidosa e/ou exigiria dependência
  (langdetect), ferindo C2. C4 fica declarativa — limitação honesta.
- **Enforçar shebang de shell via `forbid_pattern` global para C1:** auto-tripa em
  docs que citam `#!/bin/sh` como exemplo (esta própria ADR). `forbid_paths` por
  extensão evita o falso-positivo.
