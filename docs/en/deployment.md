# Deployment

## Baseline Requirements

- Production PostgreSQL/PostGIS database.
- Proper secret and environment variable management.
- Static/media strategy (`collectstatic`, media storage).
- Reverse proxy + WSGI/ASGI runtime.

## Minimal Deployment Checklist

1. Set `DJANGO_SECRET_KEY`, debug, hosts and DB variables.
2. Run migrations: `python manage.py migrate`.
3. Collect static files: `python manage.py collectstatic --noinput`.
4. Validate health endpoint: `GET /healthz/`.
5. Run smoke tests for critical APIs (scientific flow, mapbiomas, climate, mobile parity).

## Operational Endpoints

- Health check: `/healthz/`
- Integration admin panel: `/painel-admin/integracoes/`
- Integration health API: `/api/admin/integracoes/health/`
