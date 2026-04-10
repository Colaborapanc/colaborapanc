# Modules

## Backend Modules (`mapping/`)

- **Core mapping and contribution** (`views.py`, `models.py`, `forms.py`).
- **REST API and scientific flow** (`views_api.py`, serializers).
- **AR and advanced identification** (`views_ar_identificacao.py`).
- **Offline selective plants** (`views_offline_plantas.py`).
- **MapBiomas module** (`views_mapbiomas.py`, mapbiomas services).
- **Climate module** (`views_climate.py`, alert services).
- **Enrichment module** (`views_enrichment.py`, enrichment services).
- **Mobile parity module** (`views_mobile_parity.py`, `mobile_parity_service.py`).

## Mobile Modules (`mobile/src/`)

- Map and registration screens.
- Reviewer and notifications screens.
- API config and utility helpers for enrichment/offline state.

## Tests (`tests/`)

Coverage includes scientific core, permissions, integration health, enrichment pipeline, mapbiomas, plant identification, climate alerts, and mobile-relevant services.
