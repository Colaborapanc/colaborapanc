# MapBiomas API (Legacy Technical Annex)

## Status

**Rewritten and maintained as active technical annex.**
Canonical integration overview: `docs/en/integrations.md`.

## Purpose

Document operational details for MapBiomas-specific administration and troubleshooting beyond the high-level canonical integration map.

## Scope covered

- MapBiomas authentication dependencies (`MAPBIOMAS_EMAIL`, `MAPBIOMAS_PASSWORD`).
- Typical operational failure patterns (credential, token, upstream, timeout).
- Relation with admin integration health/testing surfaces.
- Expected fallback posture when MapBiomas is degraded.

## Operational references

- Service layer: `mapping/services/mapbiomas_service.py`, `mapping/services/environment/mapbiomas.py`
- API surface: `/api/mapbiomas/*`
- Admin health APIs: `/api/admin/integracoes/health/`, `/api/admin/integracoes/testar/`

## Consolidation note

Core behavior belongs in canonical docs; this annex keeps provider-specific operational depth to avoid overloading `integrations.md`.
