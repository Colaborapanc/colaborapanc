# Installation

## Scope

This guide covers local setup for:

- Backend (Django + DRF)
- Geospatial database (PostgreSQL + PostGIS)
- GIS system dependencies (GDAL)
- Mobile app (Expo/React Native)

For production deployment, see [`deployment.md`](./deployment.md).

## 1) Real prerequisites

### Host tools
- Python **3.11+**
- `pip` + virtual environment support (`venv`)
- Node.js **18+** and npm (mobile)
- PostgreSQL **15+** with PostGIS extension
- GDAL runtime/development libraries available to Python GDAL bindings

### Repository files used by this setup
- Python deps: `requirements_core.txt` (recommended) and `requirements.txt` (broader legacy set)
- Container baseline: `Dockerfile`, `docker-compose.yml`
- Django settings and env loading: `config/settings.py`

## 2) Environment variables (backend + mobile)

Django reads `.env` automatically when `python-dotenv` is available.

### Minimum backend variables for local run

```dotenv
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
POSTGRES_DB=pancdb
POSTGRES_USER=pancuser
POSTGRES_PASSWORD=pancpass123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Frequently used optional variables
- `CORS_ALLOWED_ORIGINS`
- `PLANTNET_API_KEY`
- `PLANTID_API_KEY`
- `MAPBIOMAS_EMAIL`, `MAPBIOMAS_PASSWORD`, `MAPBIOMAS_API_URL`
- `NASA_FIRMS_MAP_KEY`

### Mobile variable

```dotenv
EXPO_PUBLIC_API_URL=http://localhost:8000
```

> On a physical device, `localhost` points to the device itself. Use your machine IP or a tunnel URL.

## 3) Database and PostGIS setup

### Option A — local PostgreSQL installation
1. Create database/user.
2. Enable PostGIS in the target database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Configure `POSTGRES_*` variables accordingly.

### Option B — Docker Compose database service

```bash
docker compose up -d db
```

The compose file provisions `postgis/postgis:15-3.3` and exposes `5432`.

## 4) GIS dependencies (GDAL)

The project requires GDAL at OS level and Python package level.

Typical Linux packages:
- `gdal-bin`
- `libgdal-dev`
- `python3-gdal`

In containers, these are already installed by `Dockerfile`.

## 5) Backend setup (local, without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Default URL: `http://localhost:8000`.

## 6) Backend setup with Docker Compose

1. Create a local `.env` file (same directory as `docker-compose.yml`).
2. Set at least:
   ```dotenv
   DJANGO_SECRET_KEY=change-me
   DJANGO_DEBUG=True
   POSTGRES_DB=pancdb
   POSTGRES_USER=pancuser
   POSTGRES_PASSWORD=pancpass123
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```
3. Start services:
   ```bash
   docker compose up --build
   ```

The backend command in compose runs migrations and starts Django dev server.

## 7) Mobile setup (Expo)

```bash
cd mobile
npm install
npm start
```

Useful scripts:
- `npm run android`
- `npm run ios`
- `npm run web`
- `npm run doctor`
- `npm run test:ci`

## 8) Minimum functional flow (sanity check)

After backend is up:
1. Open `http://localhost:8000/`.
2. Validate health endpoint: `http://localhost:8000/healthz/`.
3. (Optional) Confirm API auth endpoint exists: `POST /api/token/login/`.
4. Run tests:
   ```bash
   pytest
   ```

## 9) Common errors and operational notes

### `DJANGO_SECRET_KEY not defined`
- Cause: missing variable in environment.
- Fix: define `DJANGO_SECRET_KEY` in `.env`.

### PostGIS/GIS migration error
- Cause: DB without PostGIS extension or missing GDAL libs.
- Fix: enable `postgis` extension and install GDAL system packages.

### Backend cannot connect to DB in Docker
- Common cause: using `POSTGRES_HOST=localhost` inside container.
- Fix: set `POSTGRES_HOST=db` when using compose.

### CORS issues in browser/mobile
- Fix: configure `CORS_ALLOWED_ORIGINS` with exact origins.

### Mobile cannot reach API
- Fix: set `EXPO_PUBLIC_API_URL` to host machine IP/public URL (not `localhost`) on physical devices.
