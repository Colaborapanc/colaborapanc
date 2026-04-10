# Tests

## Current set in repository
- `tests/test_scientific_core.py`
- `tests/test_permissions.py`
- `tests/test_ia_identificacao_providers.py`
- `tests/test_plant_identification.py`

## Execução
```bash
pytest
```

## Current focus
- Confidence range rules.
- Calculation of territorial score.
- Revision permission (`IsReviewerOrAdmin`).
- Normalization of the AI ​​provider pipeline.

## Gaps
- Limited coverage of DRF endpoints with real banking.
- Few integration tests between scientific flow and point status update.
- Lack of formal coverage strategy in the CI/CD pipeline of this repository.
