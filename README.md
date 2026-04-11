# ColaboraPANC

> Language selector: [English](./README.md) | [Português (Brasil)](./README.pt-BR.md)

ColaboraPANC is an open-source platform for geo-referenced mapping and scientific validation of Non-Conventional Food Plants (PANC), combining collaborative data collection, AI-assisted identification, human expert review, and environmental context integrations.

## Overview

The repository contains:

- A Django + Django REST Framework backend for web workflows and API services.
- A React Native/Expo mobile client for field and community use.
- Scientific and operational modules for enrichment, validation, climate/environmental alerts, and territorial prioritization.

## Scientific motivation

PANC records often require decentralized collection and qualified review workflows. ColaboraPANC addresses this by combining:

- citizen contributions;
- AI-assisted identification support;
- auditable human-in-the-loop validation;
- environmental and territorial analysis services.

This enables reproducible software-assisted workflows for biodiversity, food security, and agroecological mapping contexts.

## Core features

- Collaborative point registration and moderation flows.
- AI-assisted plant identification and review queue support.
- Taxonomic enrichment integrations (e.g., GBIF, iNaturalist, Tropicos, Wikimedia).
- Environmental integrations (e.g., MapBiomas and climate alert services).
- Mobile parity endpoints for map, image identification, and offline metadata access.

## Architecture overview

- **Backend:** Django project (`config/`) and core application (`mapping/`).
- **Services layer:** domain/integration services under `mapping/services/`.
- **Tests:** backend/domain tests in `tests/` and module-level tests.
- **Mobile app:** Expo/React Native app under `mobile/`.
- **Documentation:** bilingual canonical docs under `docs/en` and `docs/pt-BR`.

For structure details, see [`docs/en/project_structure.md`](./docs/en/project_structure.md).

## Technology stack

- Python + Django 4.2
- Django REST Framework
- PostgreSQL + PostGIS
- GDAL-based geospatial dependencies
- React Native + Expo (mobile)
- pytest/pytest-django (backend tests)

## Installation and quick start

### Backend (local)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Default local URL: `http://localhost:8000`.

### Mobile (local)

```bash
cd mobile
npm install
npm start
```

## Reproducible minimal workflow

1. Configure local environment from `.env.example`.
2. Run database migrations.
3. Start backend server.
4. Execute backend tests.
5. Optionally run mobile app against local API.

See reproducibility guide: [`docs/en/reproducibility.md`](./docs/en/reproducibility.md).

## Project structure

A concise structure map is available at:

- [`docs/en/project_structure.md`](./docs/en/project_structure.md)

## Documentation index

- Documentation hub: [`docs/README.md`](./docs/README.md)
- Canonical English docs: [`docs/en/index.md`](./docs/en/index.md)
- Canonical PT-BR docs: [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)

## Testing

Evaluator-focused testing instructions:

- [`docs/en/testing.md`](./docs/en/testing.md)

## Practical/scientific use cases

- Community-supported georeferenced PANC mapping.
- Expert-assisted validation of citizen-contributed records.
- Territorial/environmental support for agroecological planning.
- Educational and extension workflows connecting mobile field collection and web curation.

## Known limitations

- External provider APIs may require credentials and quota.
- Production-grade infrastructure setup is environment-specific.
- Formal archival identifiers (DOI/PID) depend on external publication workflows.

## How to cite this software

- Citation metadata guidance: [`docs/en/citation.md`](./docs/en/citation.md)
- Metadata files (to be finalized with authors): `CITATION.cff` and `codemeta.json`.

## Release and archival status

- Public release/tagging workflow is documented locally but must be executed by maintainers.
- DOI/PID assignment and archival publication are external actions and currently pending.
- SoftwareX manuscript transfer to official journal template is pending.

## Governance and project metadata

- [Contributing Guidelines](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Security Policy](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [License](./LICENSE)
