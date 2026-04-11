# ColaboraPANC

> **Language selector:** [English](./README.md) | [Português (Brasil)](./README.pt-BR.md)

ColaboraPANC is an open-source collaborative platform for georeferenced mapping of Non-Conventional Food Plants (PANC), combining collaborative contribution, AI-assisted scientific workflows, environmental monitoring, and mobile/web parity.

## What the system currently includes

### 1) Backend platform (Django + DRF)
- Web flows for map visualization, contribution, curation, moderation, and administrative panels.
- REST API endpoints for points, collaboration resources, routes, notifications, and user preferences.
- Authentication and account flows via token login, registration, and django-allauth account routes.

### 2) Scientific workflow and AI-assisted validation
- AI inference endpoint for plant identification support in scientific review.
- Review queue, per-point review detail, validation decision, and auditable decision history endpoints.
- Confidence/risk classification logic and domain-level prioritization services.

### 3) Environmental and territorial integrations
- MapBiomas alert endpoints (alerts, detail, territories, CAR/property checks, point-level analysis).
- Climate alert endpoints (active alerts, historical alerts, operational status, synchronization).
- Territorial prioritization and domain services for environmental context.

### 4) Mobile app (Expo/React Native)
- Dedicated mobile client with Expo SDK 54 and React Native 0.81.
- Mobile parity API endpoints for image identification, map previews, and offline base metadata/download.
- Device-facing scripts for Android, iOS, web, diagnostics, and CI-oriented mobile tests.

### 5) Auxiliary collaboration modules
- Notifications and push token flows.
- Conversations/messages APIs.
- Gamification, missions, rankings, and community/group experiences.
- Enrichment and integration health capabilities for external providers.

### 6) Tests and operation
- Automated test suite under `tests/` covering scientific core, permissions, enrichment, integrations, climate, environmental alerts, and related services.
- Operational routes such as healthcheck (`/healthz/`) and admin integration status/testing endpoints.

## Current technology stack

- **Backend:** Django 4.2, Django REST Framework, django-allauth.
- **Database:** PostgreSQL + PostGIS.
- **GIS dependencies:** GDAL.
- **Mobile:** Expo SDK 54, React Native 0.81.
- **Testing:** pytest + pytest-django (backend), jest/jest-expo (mobile).

## Quick start

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Default local URL: `http://localhost:8000`.

### Mobile

```bash
cd mobile
npm install
npm start
```

## Documentation entry points

- **Documentation hub:** [`docs/README.md`](./docs/README.md)
- **Canonical English index:** [`docs/en/index.md`](./docs/en/index.md)
- **Canonical Portuguese (Brazil) index:** [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)

## Project metadata

- [Contributing Guidelines](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Security Policy](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [License](./LICENSE)
