# Territorial prioritization

## Current implementation
Service: `mapping/services/priorizacao_territorial.py`.

Main function: `calcular_score_prioridade(ponto, clima_snapshot=None, densidade_validacoes=0)`.

## Formula implemented
`score_final = 0.30*incidencia + 0.25*clima + 0.25*confiabilidade + 0.20*recencia`

Components:
- **incidence**: local density of validations (simple proxy).
- **climate**: climate risk received in the snapshot (default 0.3).
- **reliability**: favors points already approved/validated.
- **recency**: recent observations are given greater weight.

## Output
Object with:
- `score` (0 to 1),
- `componentes` (details for audit),
- `explicacao` textual.

## Limitations
- Heuristics not yet calibrated with extensive historical series.
- Dependence on external climate snapshot when available.
- Current usage in sample dashboard (not full batch pipeline).
