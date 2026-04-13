# ColaboraPANC

> **Language selector:** [English](./README.md) | [Português (Brasil)](./README.pt-BR.md)

ColaboraPANC is an open-source collaborative platform for georeferenced mapping of non-conventional food plants (PANCs), integrating AI-assisted identification, expert validation, environmental monitoring, and web/mobile workflows. Its purpose is to improve the scientific usability, traceability, and territorial interpretation of citizen-contributed biodiversity records related to underutilized edible plants in Brazil.

## Target audience

- **Primary:** Researchers, biodiversity and food security teams, environmental managers, and citizen science initiatives.
- **Secondary:** Educators, extension projects, NGOs, and technical teams working with edible biodiversity and territorial monitoring.

## Main capabilities

1. Georeferenced collaborative registration of PANC observations.
2. AI-assisted plant identification support.
3. Expert validation workflow with auditable history.
4. Taxonomic enrichment from external providers.
5. Environmental and territorial monitoring integrations.
6. Mobile/web parity with API-backed workflows.

**Core workflow:** Registration → AI inference → expert review → validated record → territorial/environmental context.

## Technology stack

- **Backend:** Django 4.2 + Django REST Framework + django-allauth
- **Web frontend:** Web platform served by the Django stack / API-backed web flows
- **Mobile app:** Expo SDK 54 + React Native 0.81
- **Database:** PostgreSQL + PostGIS
- **External APIs/services:** PlantNet, Plant.id, GBIF, iNaturalist, Tropicos, Global Names, Trefle, Wikipedia, MapBiomas, INMET, NASA FIRMS, Open-Meteo
- **Infrastructure baseline:** VPS (4 GB RAM, 3 CPU cores)
- **Dependencies:** Python 3.11, PostgreSQL/PostGIS, GDAL, Node.js 18+
- **Supported OS:** Linux, macOS, Windows (via Docker)

## Quick start

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

## Testing

```bash
# Basic local backend tests
pytest

# Backend CI/CD tests with coverage
pytest tests/ mapping/tests.py --cov=mapping --cov-report=term-missing --cov-report=xml -v --tb=short

# Mobile app tests
npm run test:ci

# Backend lint/style validation
flake8 mapping/ config/ tests/ --max-line-length=120 --exclude=mapping/migrations/,__pycache__ --count --statistics
```

## Documentation

- **Documentation hub:** [`docs/README.md`](./docs/README.md)
- **Canonical English index:** [`docs/en/index.md`](./docs/en/index.md)
- **Canonical Portuguese (Brazil) index:** [`docs/pt-BR/index.md`](./docs/pt-BR/index.md)
- **Citation guide:** [`docs/en/citation.md`](./docs/en/citation.md)

## Citation, release, and DOI

- **Software name:** ColaboraPANC
- **Version:** 1.0.1
- **Release tag:** https://github.com/warleynutricionista-jpg/colaborapanc/releases/tag/1.0.1
- **Archival DOI (Zenodo):** https://doi.org/10.5281/zenodo.19546738
- **Preferred citation metadata:** [`CITATION.cff`](./CITATION.cff)

## Data availability (short statement)

The software source code is openly available. A curated demonstration dataset and repository materials are provided for inspection and reuse. Operational or user-contributed records containing sensitive geolocation or account-linked information are not publicly released.

## Project metadata

- [Contributing Guidelines](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Security Policy](./SECURITY.md)
- [Changelog](./CHANGELOG.md)
- [License](./LICENSE)
