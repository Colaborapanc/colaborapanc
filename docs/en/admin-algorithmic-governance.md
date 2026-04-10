# Administrative Annex: Algorithmic Governance

## Scope

This annex defines algorithmic governance controls for admin/reviewer operations.

## 1) Core principles
1. Assistive AI, not autonomous scientific authority.
2. Mandatory human validation for final scientific decision.
3. Auditability of prediction, review, and divergence rationale.
4. Operational transparency about uncertainty and provider limits.

## 2) Governance controls in operation
- Reviewer/admin permission boundaries on scientific endpoints.
- Separate persistence for AI prediction and human validation artifacts.
- Historical event tracking for lifecycle transitions.
- Confidence/risk-aware operational interpretation.

## 3) Supervisory governance workflow
1. Confirm inference quality context (image, metadata, provider response).
2. Validate reviewer decision path and divergence rationale when applicable.
3. Track agreement/divergence trends over time.
4. Escalate provider drift or quality regressions to operations.

## 4) Known algorithmic risks
- Region/species coverage bias in external providers.
- False positives from poor image quality.
- Upstream outages, quota limits, or provider behavior drift.
- Over-reliance risk if operators treat assistive output as final truth.

## 5) Mitigation baseline
- Continuous reviewer calibration and decision criteria refresh.
- Monitoring by confidence bands and divergence patterns.
- Structured incident handling for provider instability.
- Preserve “human-final” governance in all operational runbooks.
