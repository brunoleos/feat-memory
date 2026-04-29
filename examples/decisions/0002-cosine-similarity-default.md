---
id: ADR-0002
date: 2026-04-25
status: accepted
supersedes: null
superseded_by: null
affects_features: [F-0001]
related: []
tags: [database, vector-search, performance]
---

# ADR-0002 · Cosine similarity como métrica padrão

## Contexto

A feature `F-0001 vector-similarity-search` precisa definir uma métrica padrão para comparação vetorial. Os embeddings chegam L2-normalizados na ingestão, garantia mantida pelo pipeline externo de embedding. Isso abre três caminhos viáveis: cosine similarity, dot-product (que é equivalente a cosine quando vetores são normalizados), ou distância euclidiana.

A escolha da métrica afeta o comportamento de busca quando assumimos não-conformidade ocasional na normalização. Como a normalização é responsabilidade externa, há risco real de receber vetores não-normalizados em produção, e a métrica escolhida deve degradar de forma previsível neste caso.

## Decisão

Cosine similarity é a métrica padrão. Uma flag opcional `metric=dot_product` é exposta no endpoint para os casos em que benchmarks demonstrem ganho superior a cinco por cento em latência sem perda mensurável de qualidade.

A escolha por cosine prioriza robustez: o comportamento é previsível independente da magnitude dos vetores. Se um vetor não-normalizado entrar no sistema, o resultado ainda é interpretável, ainda que com qualidade degradada. Com dot-product puro, vetores não-normalizados produzem ranking arbitrário.

## Consequências

O comportamento é previsível independente da magnitude do vetor, o que reduz a categoria de bugs relacionados a ingestão inconsistente. A escolha é compatível com índices IVF existentes no Oracle 23ai, sem necessidade de reindex ou migração.

O custo computacional é aproximadamente três por cento maior que dot-product puro, medido em microbenchmarks isolados. Em carga real, a diferença fica diluída pelo overhead de I/O e tipicamente não é detectável no p95 de latência fim-a-fim.

## Alternativas rejeitadas

A biblioteca FastVector foi avaliada inicialmente por prometer ganho de performance significativo, mas testes em ambiente ARM (Oracle Cloud) revelaram memory leak persistente. O bug foi reportado upstream mas não há correção prevista, e a dependência é fina demais para justificar contornos.

Distância euclidiana pura foi rejeitada por instabilidade quando magnitudes variam entre documentos — comum em corpus heterogêneo. A propriedade matemática que garante boa interpretação só vale com vetores normalizados, e nesse caso o resultado é equivalente a cosine, sem ganho.

Dot-product como padrão (em vez de flag) foi rejeitado por exigir normalização garantida em todos os caminhos de ingestão. Garantir esta invariante em sistema distribuído é frágil e a falha é silenciosa: o ranking fica ruim mas o sistema não levanta erro. Cosine como padrão evita esta classe de bug.
