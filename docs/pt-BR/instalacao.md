# Instalação

## Pré-requisitos

- Python 3.11+
- PostgreSQL com extensão PostGIS
- Bibliotecas GDAL
- Node.js 18+ (para mobile)

## Setup do backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

URL local padrão: `http://localhost:8000`.

## Setup do mobile (Expo)

```bash
cd mobile
npm install
npm start
```

Scripts úteis (`mobile/package.json`):

- `npm run android`
- `npm run ios`
- `npm run web`
- `npm run doctor`

## Variáveis de ambiente

Referência detalhada nos documentos legados:
- `docs/pt/configuracao_ambiente.md`
- `docs/en/configuracao_ambiente.md`
