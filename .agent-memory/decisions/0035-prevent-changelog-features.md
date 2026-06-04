---
id: ADR-0035
date: 2026-06-04
status: accepted
version: 0.15.0
supersedes: null
superseded_by: null
affects_features: [F-0031]
related: [ADR-0028, ADR-0014, ADR-0003]
tags: [manifest, governance, quality, audit, methodology, dogfooding]
---

# ADR-0035 · prevenção em camadas contra "features-changelog"

## Contexto

F-0030 (`legacy-onboarding-polish`) era uma **feature guarda-chuva**: empacotava
seis mudanças sem relação (remoção de budget, guard de upgrade, limpeza de meta,
fix de lint, dedup, paths nativos) num único arquivo. O tell era inequívoco —
`user_value` enumerando seis coisas, A1–A6 testando seis capacidades distintas,
nome terminado em `polish`. O Manifest é por **capacidade nomeável** (ADR-0003); uma
feature que é, na prática, uma entrada de changelog corrói essa unidade.

A tentação óbvia é "um checker que detecta features incoesas". Mas coesão é um
julgamento **semântico**: distinguir "seis assuntos sem relação" de "uma capacidade
descrita em três frases" (caso de F-0027, legítimo) exige semântica, não regex.
Qualquer heurística barata para isso — contar frases do `user_value`, contar
critérios `acceptance` (F-0024 tem seis e é coeso), medir tamanho — **falsa-positiva
em features legítimas**. E um audit que dá falso-positivo mente; ADR-0014 existe
justamente para que o audit nunca minta. Construir um cohesion-checker ruidoso
violaria o princípio que a própria ferramenta defende.

ADR-0028 já estabeleceu a disciplina: **enforça onde dá (cheap + confiável), declara
onde não dá**. Esta ADR aplica isso à qualidade do Manifest.

## Decisão

Prevenção em **três camadas**, cada uma na altitude certa:

1. **Mecânica, enforced (`error`) — só o tell de alta precisão.** `validate_feature`
   bloqueia features cujo `name` contém um token de balde de changelog (conjunto
   fechado: `polish`, `misc`, `various`, `assorted`, `tweaks`, … em
   `CHANGELOG_NAME_WORDS`). Nenhuma capacidade real se chama assim, então o
   falso-positivo é ~nulo e o bloqueio hard é seguro. Pega o atalho de autoria mais
   comum: nomear o balde.

2. **Doutrinária, no momento da autoria — o "Teste de uma capacidade".** A prevenção
   que realmente morde vive onde features nascem: as skills `memory-debrief` (autoria
   diária) e `memory-deploy` (gênese). Quatro filtros antes de gravar: (a) `user_value`
   numa frase sem emendar assuntos; (b) `acceptance` coesos (mesma capacidade); (c)
   nome = substantivo de capacidade; (d) bugfix/cleanup/cosmético **não vira feature**
   — vai pro git (e ADR se for decisão). A coesão de conteúdo é resolvida aqui, por
   julgamento humano-no-loop (o debrief apresenta ao mantenedor), não por checker.

3. **Não-cobertura explícita e honesta.** **Não** existe checker mecânico de coesão de
   conteúdo, por decisão. Fingir que um regex garante coesão seria a desonestidade que
   ADR-0014 combate. "Cobertura zero honesta" onde o sinal é ruidoso.

## Consequências

Positivas: o atalho mais comum (nome-balde) é bloqueado de graça e sem ruído; o
julgamento caro (coesão) fica com o humano no ponto de criação, com a doutrina
explícita e ensinável; a ferramenta permanece coerente com a própria regra de não
mentir. Dogfood: F-0030 dissolvida; o guard de upgrade dobrou em F-0025 (mesma
capacidade); o resto virou git history + ADR-0034.

Negativas: o guard mecânico não pega features-balde com nome inocente (ex.:
`user-onboarding` empacotando seis coisas) — essas dependem da camada 2. Aceito: é o
limite real do que é mecanizável sem ruído, e a camada doutrinária cobre o resto.

## Alternativas rejeitadas

- **Checker de coesão de conteúdo (contar frases/critérios, medir tamanho, NLP):**
  ruidoso; falsa-positiva em features legítimas multi-frase (F-0027) e multi-critério
  (F-0024); erode a honestidade do audit (ADR-0014). É exatamente o tipo de validador
  vago que ADR-0028 recusou.
- **Limite de N critérios `acceptance`:** F-0024 tem seis e é coeso — proxy quebrado.
- **Guard como `warning` em vez de `error`:** o sinal de nome-balde é de altíssima
  precisão; rebaixar a warning enfraqueceria a garantia sem reduzir falso-positivo
  (que já é ~nulo).
- **Só doutrina, sem guard mecânico:** deixaria o tell mais comum e barato de pegar
  passar; a camada 1 custa quase nada e fecha o caso óbvio.
