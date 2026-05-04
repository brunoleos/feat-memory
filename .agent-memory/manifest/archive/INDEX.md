# Índice de features arquivadas

Features `shipped` e fora de `STATE.md::active_features` movidas
por `agent-memory archive --apply`. IDs continuam resolvíveis pelo
cross-check; mantenha aqui o registro histórico, sem onerar o INDEX
principal.

| ID | Nome | Status | Versão | ADRs | Depende |
|---|---|---|---|---|---|
| F-0001 | deploy | shipped | 0.3.0 | ADR-0006,ADR-0007,ADR-0011 | — |
| F-0002 | audit | shipped | 0.3.0 | ADR-0002,ADR-0003 | — |
| F-0003 | propose-adr | shipped | 0.3.0 | — | — |
| F-0004 | migrate | shipped | 0.3.0 | — | — |
| F-0005 | pre-commit-hook | shipped | 0.3.0 | ADR-0008 | F-0002 |
| F-0006 | skill-memory-deploy | shipped | 0.4.0 | ADR-0004,ADR-0010,ADR-0011 | F-0001,F-0004 |
| F-0008 | skill-memory-debrief | shipped | 0.3.0 | ADR-0004 | F-0003 |

_Gerado por `agent-memory audit` em 2026-05-04T21:41:54+00:00. Não edite manualmente._
