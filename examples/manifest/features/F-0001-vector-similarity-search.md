---
id: F-0001
name: vector-similarity-search
status: shipped
introduced: 2026-04-22
version: 0.3.0
owner: backend
user_value: >
  Permite busca semântica top-k sobre documentos indexados,
  habilitando RAG para o produto.
contracts:
  api: src/api/search.py::search_endpoint
  schemas:
    request: src/schemas/search.py::SearchRequest
    response: src/schemas/search.py::SearchResponse
  tests:
    - tests/integration/test_search.py
    - tests/unit/test_similarity.py
acceptance:
  - id: A1
    pattern: ubiquitous
    requirement: >
      O sistema deve manter todos os embeddings do índice
      L2-normalizados para que cosine seja equivalente a dot product.
  - id: A2
    pattern: event
    trigger: "search_endpoint recebe uma query embeddada com k > 0"
    response: >
      retornar os top-k documentos ordenados por cosine similarity
      em ordem decrescente
  - id: A3
    pattern: state
    state: "o índice estiver em modo de reindexação"
    response: "retornar HTTP 503 com header Retry-After de 30 segundos"
  - id: A4
    pattern: optional
    feature: "o cliente fornecer o parâmetro metric=dot_product"
    response: "usar dot product como métrica de similaridade"
  - id: A5
    pattern: unwanted
    trigger: "um vetor de magnitude zero for fornecido como query"
    response: "retornar HTTP 400 com código INVALID_QUERY_VECTOR"
  - id: A6
    pattern: unwanted
    trigger: "k for solicitado acima de 200"
    response: >
      registrar warning de degradação de recall mas executar
      a busca normalmente
depends_on: []
decisions: [ADR-0002]
metrics:
  p95_latency_ms: 120
  recall_at_10: 0.94
  last_measured: 2026-04-27
---

# F-0001 · Vector similarity search

## Comportamento

Busca top-k por cosine similarity sobre o índice IVF do Oracle 23ai. Embeddings devem chegar L2-normalizados antes da inserção; isso é responsabilidade do caminho de ingestão (não desta feature).

A query passa pelo mesmo pipeline de embedding que os documentos indexados, garantindo que o espaço vetorial seja consistente. O parâmetro `k` aceita valores entre 1 e 1000, mas valores acima de 200 disparam warning de recall degradado conforme A6.

## Limites conhecidos

A feature não suporta filtragem por metadados além de `tenant_id`, que é aplicado como predicate antes da busca vetorial. Filtros adicionais devem ser aplicados em pós-processamento pelo cliente. O escopo de filtragem mais ampla está sob avaliação em `F-0008 metadata-filtering`.

Recall degrada de forma não-linear para `k > 200` por limitação da configuração IVF do Oracle 23ai (ver `ADR-0002` para a análise de trade-off). Aplicações que precisam de top-k maior devem considerar busca em duas fases.

## Operações relacionadas

Reindex completo é feito por `scripts/reindex.py` e não é parte desta feature. Migrações de schema do índice estão documentadas em `MIGRATIONS.md`. Métricas de produção são exportadas via Prometheus na rota `/metrics`.
