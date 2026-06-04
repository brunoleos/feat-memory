---
id: ADR-0032
date: 2026-06-04
status: accepted
version: 0.14.0
supersedes: null
superseded_by: null
affects_features: [F-0028]
related: [ADR-0011, ADR-0029, ADR-0004]
tags: [methodology, skill, deploy, frontmatter, authorship, onboarding]
---

# ADR-0032 · autoria do frontmatter: o agente propõe, o humano aprova

## Contexto

Havia uma contradição direta entre dois artefatos que o agente lê durante a adoção:

- A skill `memory-deploy` era enfática: *"A skill nunca escreve no corpo da AGENTS.md
  fora do bloco. Mesmo que o usuário peça 'preencha a identidade', recuse."*
- O comentário que o próprio deploy injeta no esqueleto de frontmatter (ADR-0029)
  dizia: *"Você só precisa preencher o que está como TODO: project, stack,
  constraints."*

O agente externo que adotou o agent-memory na Tensegrams resolveu na marra ("proponho,
usuário aprova"), mas relatou a fricção: a regra estrita **não distinguia** fato
observável (project = nome do diretório; stack = detectável dos manifestos — zero
interpretação) de autoria de identidade/valores. Tratar tudo como a mesma proibição é
fricção desnecessária e empurra o agente para uma contradição entre "o audit manda
preencher o frontmatter" e "a skill me proíbe de tocar a AGENTS.md".

A proibição estrita existia para evitar **cristalização silenciosa** — o pior erro da
metodologia, em que o agente grava uma interpretação como decisão oficial sem aval
humano. Mas o antídoto correto para cristalização é o **gate de aprovação**, não a
proibição de propor. Propor a partir de evidência e apresentar para aprovação preserva
o aval humano sem deixar o frontmatter órfão.

## Decisão

O agente **pode (e deve) propor o frontmatter inteiro** — `project`, `stack` e
`constraints` — a partir de evidência observável do projeto, e **apresentá-lo ao
mantenedor para aprovação** antes de gravar. Nunca grava valores não-aprovados. O gate
é aprovação humana, não proibição.

1. **Fontes de proposta, por grau de interpretação:**
   - `project` — fato observável (nome do diretório/repositório); proponha direto.
   - `stack` — detectável de manifestos (`package.json`, `pyproject.toml`, …) e da
     estrutura; proponha `language`/`architecture`/deps observados.
   - `constraints` — **rascunhadas** de evidência mecânica: configs de lint/formatter,
     gates de CI, deps fixadas/evitadas, e lições já escritas em prosa. Cada uma com
     `id`, `severity` e `rule`, marcada explicitamente como rascunho.

2. **O gate é aprovação.** Gravar valores não-aprovados como se fossem decisão oficial
   é tão grave quanto cristalizar um ADR sem revisão. A skill apresenta a proposta
   inteira; o mantenedor revisa, edita e aprova; só então grava.

3. **Coerência dos três artefatos.** A skill (`memory-deploy`), o comentário injetado
   no esqueleto (ADR-0029) e a descrição da skill no bloco da AGENTS.md passam a dizer
   a mesma coisa: *propõe a partir de evidência, humano aprova*.

4. **Refina, não revoga, ADR-0011.** O deploy mecânico continua não autorando
   identidade sozinho; a prosa de identidade/convenções fora do frontmatter segue sendo
   autoria humana. O que muda é que a **skill** pode propor o frontmatter estruturado
   (que antes ficava órfão) sob o gate de aprovação.

## Consequências

Positivas: some a contradição que travava o agente; a adoção legacy flui (o frontmatter
é proposto a partir do código, não deixado em branco); o gate de aprovação preserva o
princípio anti-cristalização; fato observável deixa de ser tratado como autoria de
identidade.

Negativas: exige disciplina do agente para marcar constraints inferidas como rascunho e
não confundir proposta com decisão; um mantenedor desatento pode aprovar por cansaço
(mitigado pela mesma doutrina de "lote pequeno, revisão crítica" da gênese).

## Alternativas rejeitadas

- **Manter a proibição estrita e só corrigir o comentário injetado:** preservava a
  fricção (frontmatter órfão; fato observável tratado como identidade) — o problema que
  esta ADR resolve.
- **Deixar o deploy preencher o frontmatter automaticamente, sem aprovação:** seria
  cristalização silenciosa mecânica — exatamente o que a metodologia combate.
- **Distinguir só "fato observável (propõe) vs identidade (humano)":** opção
  intermediária considerada; o mantenedor preferiu a versão mais automação-forward
  (propor inclusive constraints, sempre sob aprovação), que cobre o caso observável e
  ainda acelera o trabalho mais caro (rascunhar constraints do tooling).
