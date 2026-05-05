"""Camada de governança: enforcement, telemetria, hooks, métricas.

Inclui audit (orquestrador), telemetry, check-staleness, check-version-bump,
install-hooks.

Importa de `agent_memory.shared` e `agent_memory.memory` (precisa dos
schemas para validar). Nunca é importada por `agent_memory.memory` —
ADR-0021 fixa essa direção, garantindo que `deploy --no-hooks` produz
operação puramente memória.
"""
