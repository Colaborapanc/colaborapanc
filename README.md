# ColaboraPANC

> **Language / Idioma:** [English](./README.md) | [Português (Brasil)](./README.pt-BR.md)

ColaboraPANC is an open-source collaborative platform for georeferenced mapping of Non-Conventional Food Plants (PANC), with AI-assisted identification, human review workflows, and environmental/territorial analysis.

## Project Overview

ColaboraPANC combines:
- A Django + Django REST Framework backend for web and API workflows.
- A PostgreSQL/PostGIS geospatial data layer.
- An Expo/React Native mobile app.
- Integration services for plant identification, taxonomic enrichment, climate alerts, and MapBiomas environmental alerts.

## Current Core Capabilities

- Georeferenced PANC point submission and curation.
- Scientific workflow: AI inference, review queue, validation decision, and decision history.
- Mobile parity endpoints for image identification and offline base metadata/download.
- Environmental and territorial modules (MapBiomas, climate alerts, territorial prioritization).
- Auxiliary modules for notifications, conversations/messages, routes, and user preferences.

## Technology Stack

- **Backend:** Django 4.2, Django REST Framework, django-allauth.
- **Database:** PostgreSQL + PostGIS.
- **GIS dependencies:** GDAL.
- **Mobile:** Expo SDK 54 + React Native.
- **Tests:** pytest + pytest-django.

## Quick Start

### Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Mobile

```bash
cd mobile
npm install
npm start
```

## Documentation

- **English documentation index:** [`docs/en/index.md`](./docs/en/index.md)
- **Portuguese documentation index:** [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)
- **Docs hub:** [`docs/README.md`](./docs/README.md)

## Project Metadata

- [Contributing Guidelines](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Security Policy](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [License](./LICENSE)
