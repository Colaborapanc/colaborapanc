# Instalação do backend

## Requisitos
- Python 3.11+
- PostgreSQL + PostGIS
- GDAL (headers e binários)

## 1) Ambiente Python
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements_core.txt
```

> Em ambientes que usam o conjunto completo de dependências, substitua para `requirements.txt`.

## 2) Banco de dados
Crie banco e usuário PostgreSQL e ative `postgis` no banco alvo.

## 3) Variáveis de ambiente
Exemplo mínimo:
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

## 4) Migrações e usuário admin
```bash
python manage.py migrate
python manage.py createsuperuser
```

## 5) Execução local
```bash
python manage.py runserver 0.0.0.0:8000
```

## 6) Verificação rápida
```bash
python manage.py check
curl http://127.0.0.1:8000/healthz/
```

## Notas
- Sem `DJANGO_SECRET_KEY`, o backend não inicia.
- O engine do banco é PostGIS; banco sem extensão geoespacial quebra migrações/queries GIS.
