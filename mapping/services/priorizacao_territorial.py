"""Compatibilidade retroativa do serviço de priorização territorial.

Este módulo permanece para evitar quebra de imports legados.
A implementação oficial foi movida para:
`mapping.domains.territorial.prioritization`.
"""

from mapping.domains.territorial.prioritization import (
    PriorizacaoResultado,
    calcular_score_prioridade,
)

__all__ = ["PriorizacaoResultado", "calcular_score_prioridade"]
