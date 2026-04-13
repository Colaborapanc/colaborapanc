# AI Governance

## Principles adopted
1. Assistive, not autonomous AI.
2. Mandatory human review by authorized role.
3. Auditable record of decisions and disagreements.
4. Transparency about uncertainty and limits of external providers.

## Technical controls present
- Revision access control: `IsReviewerOrAdmin`.
- Persistence of prediction and validation in separate models.
- Event history (`HistoricoValidacao`).
- Confidence rating and operational recommendation.

## Known risks
- Bias and uneven coverage of external APIs by region/species.
- False positives in low quality images.
- Dependence on third party availability/quotas.

## Recommended mitigations
- Continuous training of reviewers.
- Divergence monitoring panels by provider.
- Collection context record (image quality, plant organ).
