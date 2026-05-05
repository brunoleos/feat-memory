"""Camada de memória: artefatos canônicos da metodologia.

Inclui schemas, geração de índices, ciclo de vida (archive, checkpoints,
migrate, propose-adr) e os templates/skills.

Importa apenas de `agent_memory.shared` e `agent_memory.__version__`.
Nunca importa de `agent_memory.governance` — essa direção é proibida
pela ADR-0021 e quebra a garantia de que `deploy --no-hooks` produz
operação puramente memória.
"""
