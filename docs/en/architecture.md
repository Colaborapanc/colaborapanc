# Architecture

## High-Level Components

1. **Web/API Backend**: Django project (`config/`, `mapping/`).
2. **Geospatial Data Layer**: PostgreSQL + PostGIS.
3. **Mobile App**: Expo + React Native (`mobile/`).
4. **Integration Layer**: plant ID, enrichment, climate and environmental services.

## Main Functional Flows

- Point lifecycle: submission → AI inference → review → validation.
- Environmental analysis: climate snapshots + MapBiomas alerts.
- Mobile parity: shared service logic for web/mobile identification and offline metadata.

## Key Source References

- URL composition: `config/urls.py`, `mapping/urls.py`.
- Domain model: `mapping/models.py`.
- Core services: `mapping/services/`.
- API/web views: `mapping/views.py`, `mapping/views_api.py`, and specialized `views_*` files.
