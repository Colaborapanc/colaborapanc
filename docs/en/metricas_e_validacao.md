# Metrics and validation

## Source endpoint
`GET /api/cientifico/dashboard/`

## Metrics available today
- Total points submitted.
- Total points with image.
- Total inferences.
- Validation and rejection rate.
- Agreement and divergence AI vs expert (top-1).
- Average time until validation (hours).
- Geographic distribution by state.
- Top suggested species.
- Distribution by trust (`alta`, `media`, `baixa`).
- Sample of territorial prioritization.

## How to interpret
- **High agreement** does not replace human review; it only indicates AI-expert proximity in the validated set.
- **High average time** indicates a review bottleneck.
- **Confidence distribution** helps monitor operational quality of inference.

## Planned metrics (not implemented in current code)
- Precision, recall, F1 by species and by biome.
- Curves by provider and time window.
- Consolidated confusion matrix.
