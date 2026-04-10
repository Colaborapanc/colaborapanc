# API

## Base

Local base URL: `http://localhost:8000`.

## Authentication and Accounts

- `POST /api/token/login/`
- `POST /api/register/`
- `/accounts/*` (django-allauth)

## Core API Groups

- **Points and collaboration**: `/api/pontos/`, `/api/compartilhamentos/`
- **Scientific flow**:
  - `/api/cientifico/pontos/<id>/inferencia/`
  - `/api/cientifico/revisao/fila/`
  - `/api/cientifico/pontos/<id>/validacao/`
  - `/api/cientifico/dashboard/`
- **Mobile parity**:
  - `/api/mobile/identificacao/imagem/`
  - `/api/mobile/mapa/previews/`
  - `/api/mobile/offline/base/metadata/`
- **MapBiomas**: `/api/mapbiomas/*`
- **Climate**: `/api/clima/*`, `/api/alertas-ativos/`
- **Enrichment**: `/api/enriquecimento/*`

## Full Route Source of Truth

Use `mapping/urls.py` as the authoritative route registry.
