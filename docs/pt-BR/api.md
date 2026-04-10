# API

## Base

Base local: `http://localhost:8000`.

## Autenticação e contas

- `POST /api/token/login/`
- `POST /api/register/`
- `/accounts/*` (django-allauth)

## Grupos principais de API

- **Pontos e colaboração**: `/api/pontos/`, `/api/compartilhamentos/`
- **Fluxo científico**:
  - `/api/cientifico/pontos/<id>/inferencia/`
  - `/api/cientifico/revisao/fila/`
  - `/api/cientifico/pontos/<id>/validacao/`
  - `/api/cientifico/dashboard/`
- **Paridade mobile**:
  - `/api/mobile/identificacao/imagem/`
  - `/api/mobile/mapa/previews/`
  - `/api/mobile/offline/base/metadata/`
- **MapBiomas**: `/api/mapbiomas/*`
- **Clima**: `/api/clima/*`, `/api/alertas-ativos/`
- **Enriquecimento**: `/api/enriquecimento/*`

## Fonte de verdade de rotas

Usar `mapping/urls.py` como registro autoritativo de endpoints.
