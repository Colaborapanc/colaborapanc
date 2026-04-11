# Reproducibility Guide

## Scope

This guide describes a minimal reproducible workflow using local repository resources only.

## Prerequisites

- Python environment for backend
- PostgreSQL/PostGIS available locally
- Node.js/npm for mobile (optional)
- Environment variables configured from `.env.example`

## Minimal backend workflow

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
cp .env.example .env
python manage.py migrate
python manage.py test tests
```

Optional local run:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Data reproducibility status

- No formal public dataset package is asserted in this repository yet.
- Data scaffolding is documented under `data/`.
- Any external dataset deposit must be documented after maintainers approve provenance and licensing.

## External dependencies caveat

Some integrations require external credentials/services (e.g., enrichment APIs, alert providers).
For deterministic local checks, use test paths and mocked flows where available.
