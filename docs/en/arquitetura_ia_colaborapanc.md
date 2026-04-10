# ColaboraPANC AI architecture

## Purpose of the AI ​​layer
Provide **assistive suggestion** for botanical identification from images, with confidence score, top-k and auditable trail for human review.

## Implemented components

### 1) Inference Orchestration
- Module in `mapping/services/ia_identificacao/` with:
- `factory.py` to instantiate providers.
- `plantnet_provider.py` and `plantid_provider.py`.
- `schemas.py` for normalization (`ResultadoInferencia`, `PredicaoNormalizada`).
- Exposed function: `identificar_com_multiplos_provedores(...)`.

### 2) Execution endpoint
- `POST /api/cientifico/pontos/<ponto_id>/inferencia/`
- Implemented in `InferenciaPontoAPIView`.
- Requirements:
- existing point,
- valid image,
- authentication.

### 3) Scientific storage
- `PredicaoIA`: structured inference result.
- `ValidacaoEspecialista`: final human decision.
- `HistoricoValidacao`: auditable cycle events.

## How inference works
1. Receive a photo of the point.
2. Query configured providers (PlantNet mandatory, Plant.id when key available).
3. Normalizes results to top-k.
4. Defines global score and operational range (`alto`, `medio`, `baixo`).
5. Mark whether human review is required.
6. Updates suggested fields in the point.

## Operational definitions
- **Top-k**: list of the k most likely hypotheses (in the current code, up to 3).
- **Confidence score**: continuous value (0–1 internally; also persisted in % at the point).
- **Risk/reliability range**:
- high: score ≥ 0.85
- average: 0.60 ≤ score < 0.85
- low: score < 0.60

## Explainability available
- Textual justification by prediction (`justificativa`).
- Components of the territorial score on the dashboard (`componentes`).
- History of events in `HistoricoValidacao`.

## Current limitations
- Dependency on third-party APIs and valid keys.
- Lack of own model trained locally in the backend.
- No formal statistical calibration of confidence by species/biome.

## Governance principle
AI **does not decide alone**. Final validation decisions are human via the reviewer/admin role.
