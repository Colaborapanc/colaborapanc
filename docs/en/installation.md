# Installation

## Prerequisites

- Python 3.11+
- PostgreSQL with PostGIS extension
- GDAL libraries
- Node.js 18+ (for mobile)

## Backend Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Default local URL: `http://localhost:8000`.

## Mobile Setup (Expo)

```bash
cd mobile
npm install
npm start
```

Useful scripts (`mobile/package.json`):

- `npm run android`
- `npm run ios`
- `npm run web`
- `npm run doctor`

## Environment Variables

Check the environment reference in legacy detailed docs:
- `docs/en/configuracao_ambiente.md`
- `docs/pt/configuracao_ambiente.md`
