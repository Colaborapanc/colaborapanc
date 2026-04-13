# Backend installation

## Requirements
- Python 3.11+
- PostgreSQL + PostGIS
- GDAL (headers and binaries)

## 1) Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements_core.txt
```

> In environments that use the full set of dependencies, replace this with `requirements.txt`.

## 2) Database
Create a PostgreSQL database and user and activate `postgis` on the target database.

## 3) Environment variables
Minimal example:
```env
DJANGO_SECRET_KEY=troque-esta-chave
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=pancdb
POSTGRES_USER=pancuser
POSTGRES_PASSWORD=senha
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

PLANTNET_API_KEY=
PLANTID_API_KEY=
```

## 4) Migrations and admin user
```bash
python manage.py migrate
python manage.py createsuperuser
```

## 5) Local execution
```bash
python manage.py runserver 0.0.0.0:8000
```

##6) Quick Check
```bash
python manage.py check
curl http://127.0.0.1:8000/healthz/
```

## Notes
- Without `DJANGO_SECRET_KEY`, the backend does not start.
- The bank's engine is PostGIS; bank without geospatial extension breaks GIS migrations/queries.
