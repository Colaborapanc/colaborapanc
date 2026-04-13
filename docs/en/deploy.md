# Deploy

## Minimum requirements
- PostgreSQL/PostGIS available and accessible.
- Configured production environment variables.
- Python and geospatial dependencies installed.
- Static file and media strategy (`collectstatic`, storage).

## Base step by step (backend)
1. Provision Linux environment with Python and GDAL.
2. Configure PostGIS database.
3. Define production `.env` (`DEBUG=False`).
4. Install dependencies and run migrations.
5. Run `collectstatic`.
6. Upload application with WSGI (`config/wsgi.py`) via Gunicorn/uWSGI and reverse proxy.

## Mobile
- Build Expo according to the (preview/prod) environment, with `EXPO_PUBLIC_API_URL` pointing to the public backend.

## Care
- Review CORS/CSRF with official hosts.
- Mandatory TLS certificates.
- Backup policy for banking and media.
- Rotation of secrets and API keys.
