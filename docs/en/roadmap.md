# Roadmap

## Scope and honesty model

This roadmap separates what is:
- **Implemented** (active in current baseline),
- **Partially implemented** (usable with clear limitations),
- **In consolidation** (stabilization/hardening of existing capabilities),
- **Future** (planned direction, not committed delivery date).

## 1) Implemented

- Scientific flow with assistive inference, review queue, and human validation lifecycle.
- Integration operational health surfaces (panel + admin APIs).
- Mobile parity endpoints and online/offline field support baseline.
- Environmental domain integrations (MapBiomas/climate context) and monitoring-related flows.
- Canonical bilingual documentation structure (`docs/en` + `docs/pt-BR`).

## 2) Partially implemented

- Advanced identification resources (multi-source fallback paths) with provider/config dependency.
- Mobile selective offline package and advanced auto-detection support with operational constraints.
- Some integration probes where verification depth is limited by current contract/provider constraints.
- Legacy/coexisting endpoint families still under harmonization.

## 3) In consolidation (near-term focus)

- Improve observability quality (clearer incident diagnostics, latency/failure trends, and operational playbooks).
- Strengthen review-governance metrics (agreement/divergence interpretation and reviewer support signals).
- Expand regression coverage for sensitive boundaries (permissions, integrations, scientific lifecycle edge cases).
- Continue canonical-doc cleanup while reducing legacy overlap.

## 4) Future direction

- Stronger quality analytics for scientific validation outcomes (beyond basic dashboard counters).
- Better operator tooling for cross-domain incident triage (identification, enrichment, climate/environment).
- Progressive domain modularization to reduce concentration in the `mapping` app.
- Further UX refinement for mobile field workflows in constrained-connectivity contexts.

## 5) Delivery expectations

- Items in “Implemented” are baseline.
- “Partially implemented” items should be treated as operationally available but bounded.
- “In consolidation” items are active priorities and may land incrementally.
- “Future” items are directional and may change based on scientific/operational priorities.
