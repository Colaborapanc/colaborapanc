# Testes

## Conjunto atual no repositório
- `tests/test_scientific_core.py`
- `tests/test_permissions.py`
- `tests/test_ia_identificacao_providers.py`
- `tests/test_plant_identification.py`

## Execução
```bash
pytest
```

## Foco atual
- Regras de faixa de confiança.
- Cálculo de score territorial.
- Permissão de revisão (`IsReviewerOrAdmin`).
- Normalização do pipeline de provedores de IA.

## Lacunas
- Cobertura limitada de endpoints DRF com banco real.
- Poucos testes de integração entre fluxo científico e atualização de status de ponto.
- Ausência de estratégia de cobertura formal no pipeline CI/CD deste repositório.
