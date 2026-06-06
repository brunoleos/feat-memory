"""Utilitários compartilhados sem opinião sobre memória ou governança.

Apenas stdlib + pyyaml. Nenhum módulo do projeto deve ser importado aqui
(verificável mecanicamente).

ADR-0021 fixa a regra de dependência hierárquica:
    shared ⇐ memory ⇐ governance
"""
