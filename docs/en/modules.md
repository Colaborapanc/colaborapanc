# Modules

## Scope

This canonical module map documents current functional organization across backend, mobile, and test layers.

## 1) Backend modules by domain (`mapping/`)

### 1.1 Platform, routing, and web/API surface
- `mapping/urls.py`: route composition for web pages, admin tools, REST routers, scientific APIs, climate, mapbiomas, enrichment, mobile parity, and offline endpoints.
- `mapping/views.py`: web pages + mixed legacy/operational API endpoints.
- `mapping/views_api.py`: REST/scientific APIs (review queue, inference, validation, dashboard, communication/resources viewsets).
- Specialized views:
  - `mapping/views_ar_identificacao.py`
  - `mapping/views_offline_plantas.py`
  - `mapping/views_mapbiomas.py`
  - `mapping/views_climate.py`
  - `mapping/views_enrichment.py`
  - `mapping/views_mobile_parity.py`

### 1.2 Core scientific and botanical domain
- Models:
  - `PontoPANC` (georeferenced observation lifecycle)
  - `PlantaReferencial` (canonical species base)
  - `PredicaoIA`, `ValidacaoEspecialista`, `HistoricoValidacao`
  - enrichment history entities (`HistoricoEnriquecimento`, `EnriquecimentoTaxonomicoHistorico`)
- Services:
  - `mapping/services/ia_identificacao.py` + `mapping/services/ia_identificacao/*`
  - `mapping/services/plant_identification_service.py`
  - `mapping/services/enrichment/*`

### 1.3 Environmental and territorial domain
- Environmental APIs and sync:
  - `mapping/views_mapbiomas.py`, `mapping/views_climate.py`
  - `mapping/services/mapbiomas_service.py`, `mapping/services/mapbiomas_alert_service.py`
  - `mapping/services/weather/inmet.py`, `mapping/services/weather/open_meteo.py`
  - `mapping/services/nasa_firms_service.py`
- Territorial prioritization:
  - domain engine `mapping/domains/territorial/prioritization.py`
  - compatibility facade `mapping/services/priorizacao_territorial.py`

### 1.4 Collaboration, communication, and community domain
- Communication models/endpoints:
  - `Notificacao`, `DispositivoPush`, `Conversa`, `Mensagem`
  - related viewsets in `views_api.py` and `views.py`
- Community/gamification:
  - `Badge`, `Missao`, `MissaoUsuario`, `PontuacaoUsuario`, `RankingRevisor`, `Grupo`, `Evento`
  - mission/ranking/admin flows in `views.py`

### 1.5 Routes, recommendations, sharing, and commerce domain
- Routes and itinerary:
  - `Rota`, `RotaPonto`, `RoteiroPANC`, `RoteiroPANCItem`
  - route calculations in `mapping/services/rotas_service.py`
- Recommendation and sharing:
  - `RecomendacaoPANC`, `CompartilhamentoSocial`
  - recommendation logic in `mapping/services/recomendacao_ml.py`
- External commerce entities:
  - `IntegracaoEcommerce`, `ProdutoSemente`, `LojaExterno`, `ProdutoExterno`

### 1.6 AR, offline, and mobile parity domain
- AR entities and endpoints:
  - `PlantaCustomizada`, `ModeloAR`, `HistoricoIdentificacao`, `ReferenciaAR`
  - `mapping/views_ar_identificacao.py`
- Offline entities and endpoints:
  - `PacotePlantasOffline`, `PlantaOfflineUsuario`, `ConfiguracaoOffline`, `CacheOffline`
  - `mapping/views_offline_plantas.py`
- Mobile parity contract:
  - `mapping/services/mobile_parity_service.py`
  - `mapping/views_mobile_parity.py`

### 1.7 Integrations observability and operational tooling
- Integration health and probes:
  - `mapping/services/integrations/healthcheck.py`
  - `mapping/services/integration_health.py`
  - admin-facing health endpoints in `views.py`
- Management commands under `mapping/management/commands/` for sync/import/backfill/audit tasks.

## 2) Cross-cutting backend modules

- `mapping/serializers.py`: DTO and payload normalization for APIs.
- `mapping/permissions.py`: reviewer/admin permission boundary.
- `mapping/signals.py`: event-triggered behavior (e.g., gamification progression).
- `mapping/forms.py` and templates for web form/UI workflows.

## 3) Mobile modules (`mobile/src/`)

### 3.1 API and communication layer
- `mobile/src/config/api.js`: canonical mobile endpoint registry and API base resolution.
- HTTP/auth and communication services:
  - `httpClient.js`, `apiClient.js`, `authService.js`, `comunicacaoService.js`, `mensagensService.js`, `notificacoesService.js`.

### 3.2 Feature services
- Botanical/scientific services:
  - `identificacaoService.js`, `aiAssistService.js`, `enrichmentService.js`, `enriquecimentoService.js`.
- Offline/sync services:
  - `offlineService.js`, `offlineStorage.js`, `plantasOfflineService.js`, `speciesFocusService.js`, `autoDetectionService.js`.
- Routes/sharing/other utilities:
  - `rotasService.js`, `compartilhamentoService.js`, `droneMissionService.js`, `i18nService.js`.

### 3.3 UI/screen modules
- Core screens: map, registration, contribution detail, reviewer, identification, notifications, profile, offline plants/settings.
- Screens live in `mobile/src/screens/` and consume services as the primary backend integration boundary.

## 4) Test modules (`tests/`)

Current test suite is organized by behavior/contract domains:
- scientific core and IA providers,
- permissions,
- enrichment pipeline and wikipedia enrichment,
- integration health and status utils,
- climate/environmental alerts,
- mapbiomas integration,
- territorial prioritization domain,
- point registration/autocomplete flow.

## 5) Domain interaction summary

1. Views receive HTTP requests and call serializers/services.
2. Service/domain modules perform business rules, integrations, and normalization.
3. Models persist lifecycle state and audit artifacts.
4. Mobile consumes stable API contracts and parity endpoints.
5. Tests validate critical cross-domain contracts and regression-prone paths.
