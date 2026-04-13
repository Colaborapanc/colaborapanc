# Deployment

## Scope

This guide covers production-oriented deployment for:

- Backend application runtime
- PostgreSQL/PostGIS database
- GIS dependencies and static/media handling
- Containerized and non-containerized approaches
- Mobile app backend targeting

For local developer setup, see [`installation.md`](./installation.md).

## 1) Production prerequisites

### Infrastructure baseline
- Linux host/VM/container platform
- Python 3.11 runtime (if not containerized)
- PostgreSQL with PostGIS enabled
- Reverse proxy (e.g., Nginx) in front of Django app server
- TLS certificates for public endpoints

### Application baseline
- Environment variables defined securely (no plaintext secrets in repo)
- `DJANGO_SECRET_KEY` set
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS` set for real domains/IPs
- Database variables (`POSTGRES_*`) aligned with production database

## 2) Environment variables checklist

### Mandatory in production
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT` (if non-default)

### Strongly recommended
- `CORS_ALLOWED_ORIGINS`
- Email backend variables (`EMAIL_HOST`, `EMAIL_PORT`, etc.)
- Integration keys only when corresponding services are enabled

## 3) Database and migration flow

1. Provision PostgreSQL/PostGIS.
2. Enable PostGIS extension on target database.
3. Ensure app credentials can connect.
4. Run schema migrations:
   ```bash
   python manage.py migrate --noinput
   ```
5. Validate startup and critical queries.

## 4) Static/media and app process

Run static collection on each deploy:

```bash
python manage.py collectstatic --noinput
```

Run Django using Gunicorn (as in Dockerfile default CMD):

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

Use reverse proxy for:
- TLS termination
- Static/media serving strategy
- Request buffering/timeouts and header policy

## 5) Containerized deployment reference

### Build and run

```bash
docker compose up --build -d
```

### Important compose/runtime note
- `config/settings.py` consumes `POSTGRES_HOST`, not `DB_HOST`.
- In containerized setups, set `POSTGRES_HOST=db` in `.env`.

### Data durability
Persist DB and media/static volumes (already declared in `docker-compose.yml`):
- `postgres_data`
- `static_files`
- `media_files`

## 6) Operational smoke checks after deploy

- Health check: `GET /healthz/`
- App root loads: `GET /`
- Admin route responds: `GET /admin/`
- Integration panel/API:
  - `GET /painel-admin/integracoes/`
  - `GET /api/admin/integracoes/health/`
- Optional API smoke:
  - `POST /api/token/login/`
  - `GET /api/alertas-ativos/`

## 7) Mobile release alignment

Set mobile environment to public backend URL:

```dotenv
EXPO_PUBLIC_API_URL=https://your-api-domain
```

Do not publish mobile builds pointing to localhost/private-only hostnames.

## 8) Common deployment issues

### `ImproperlyConfigured: DJANGO_SECRET_KEY ...`
- Cause: missing secret in runtime environment.
- Fix: inject `DJANGO_SECRET_KEY` via secret manager or `.env`.

### Database connection refused
- Cause: invalid `POSTGRES_HOST`/network/firewall.
- Fix: validate DB host, credentials, port, and network reachability.

### GIS/PostGIS failures
- Cause: PostGIS extension missing or GDAL runtime mismatch.
- Fix: enable extension and ensure GDAL packages/libraries are available.

### CORS/CSRF errors in production
- Cause: domains not listed in allowed hosts/origins.
- Fix: set `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` explicitly.

### Static files not served
- Cause: missing `collectstatic` step or reverse proxy static mapping.
- Fix: rerun `collectstatic` and validate server/proxy static configuration.
