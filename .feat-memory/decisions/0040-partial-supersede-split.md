---
id: ADR-0040
date: 2026-06-25
status: accepted
version: 1.4.0
supersedes: null
superseded_by: null
affects_features: []
related: [ADR-0023]
tags: [decisions, governance, supersede]
---

# ADR-0040 · Supersede parcial: dividir o base em ADRs novos

## Contexto

O modelo de supersede assume substituição **total** ([ADR-0023](0023-superseded-decisions-folder.md)): o base ganha `status: superseded` + `superseded_by`, vai para `decisions/superseded/`, e o sucessor aponta `supersedes`. Quando uma decisão nova invalida só **parte** de um ADR, o caminho ingênuo deixaria o base "meio-válido" — parte obsoleta e parte vigente convivendo no mesmo arquivo imutável. Quem lê o INDEX vê `accepted` e não sabe que metade caducou; o ADR vira ambíguo e não-confiável.

## Decisão

Supersede parcial vira **supersede total + split**. Marca-se o base **inteiro** como `superseded` e divide-se o conteúdo em ADRs novos: um capturando a decisão nova, outro(s) re-afirmando a parte que continua válida. O `superseded_by` do base lista **todos** os sucessores (o campo já é livre no schema — [schemas.py](../../src/feat_memory/memory/schemas.py) — e aceita lista sem mudança de código). Invariante resultante: **todo ADR vigente é verdadeiro por inteiro, nunca parcialmente falso.** Aceita-se a cerimônia extra de reescrever a parte mantida em troca de ADRs ativos sem ambiguidade.

## Alternativas rejeitadas

- **Editar o base removendo só a parte obsoleta**: viola a imutabilidade do `accepted` (METHODOLOGY §4) — ADR editável é anotação, não registro histórico.
- **Manter o base parcialmente válido com nota inline**: o leitor do INDEX vê `accepted` e não percebe a caducidade parcial; um `superseded_by` "parcial" não tem onde morar no schema.
- **Checker no audit**: o grafo de supersede parcial não tem verificação barata e confiável (mesma razão de C3/C4 ficarem declarativas); a regra fica normativa-manual, como o supersede já é.
