# Architecture

## Scope

This canonical document describes the current ColaboraPANC architecture based on active code in:

- `config/*`
- `mapping/models.py`
- `mapping/views*.py`
- `mapping/services/*` and `mapping/domains/*`
- `mapping/urls.py`
- `mobile/src/*`
- `tests/*`

## 1) System overview

ColaboraPANC is structured as four connected layers:

1. **Web/API backend (Django + DRF)**
   - HTTP entrypoint and URL composition in `config/urls.py` and `mapping/urls.py`.
   - Domain models, web views, REST endpoints, and orchestration services under `mapping/`.
2. **Geospatial data layer (PostgreSQL + PostGIS)**
   - Django GIS engine configured via `django.contrib.gis.db.backends.postgis`.
   - Core georeferenced entity: `PontoPANC` with geographic point and validation lifecycle fields.
3. **Mobile client (Expo/React Native)**
   - Mobile app services and screens under `mobile/src/`.
   - API endpoint contracts centralized in `mobile/src/config/api.js`.
4. **External integration layer**
   - Scientific identification (PlantNet/Plant.id).
   - Taxonomic enrichment (Global Names, Tropicos, GBIF, iNaturalist, Trefle, Wikimedia).
   - Environmental monitoring (MapBiomas, INMET, Open-Meteo, NASA FIRMS).

## 2) Backend architecture

### 2.1 Configuration and runtime boundary
- `config/settings.py` controls env loading, security, PostGIS database, static/media, DRF and optional CORS.
- `config/urls.py` exposes admin, app routes, allauth routes, and `healthz` operational endpoint.

### 2.2 URL topology and API composition
- `mapping/urls.py` composes:
  - web pages and admin panels,
  - router-based REST viewsets (`/api/`),
  - scientific endpoints (`/api/cientifico/*`),
  - environmental endpoints (`/api/mapbiomas/*`, `/api/clima/*`, `/api/alertas-ativos/`),
  - enrichment (`/api/enriquecimento/*`),
  - mobile parity (`/api/mobile/*`),
  - offline species workflows (`/api/plantas-offline/*`, `/api/especies-referenciais/*`).

### 2.3 Model architecture and principal entities

#### Core scientific/geospatial entities
- `PontoPANC`: georeferenced observation and central lifecycle state.
- `PlantaReferencial`: canonical plant catalog with enriched fields.
- `PredicaoIA`: persisted AI prediction payload and confidence context.
- `ValidacaoEspecialista`: final human validation decision.
- `HistoricoValidacao`: audit trail for scientific lifecycle events.
- `HistoricoEnriquecimento` and `EnriquecimentoTaxonomicoHistorico`: traceability of enrichment runs.

#### Collaboration and ecosystem entities
- Communication: `Notificacao`, `DispositivoPush`, `Conversa`, `Mensagem`.
- Gamification/community: `Badge`, `Missao`, `MissaoUsuario`, `PontuacaoUsuario`, `RankingRevisor`, `Grupo`, `Evento`.
- Routes and sharing: `Rota`, `RotaPonto`, `CompartilhamentoSocial`, `RoteiroPANC`, `RoteiroPANCItem`.
- AR/offline: `PlantaCustomizada`, `ModeloAR`, `ReferenciaAR`, `PacotePlantasOffline`, `PlantaOfflineUsuario`, `ConfiguracaoOffline`, `CacheOffline`.

## 3) Service and domain architecture

### 3.1 Service layer roles
- `mapping/services/ia_identificacao*`: AI provider orchestration and normalization.
- `mapping/services/enrichment/*`: taxonomic enrichment pipeline (providers, confidence, normalization, cache, orchestration).
- `mapping/services/mobile_parity_service.py`: canonical payload contracts for web/mobile parity.
- `mapping/services/integrations/healthcheck.py`: active integration probes and operational status.
- `mapping/services/environment*`, `mapbiomas*`, `weather/*`, `nasa_firms_service.py`: environmental data ingestion.

### 3.2 Domain-level evolution
- Territorial prioritization logic is versioned in `mapping/domains/territorial/prioritization.py` with compatibility facade in `mapping/services/priorizacao_territorial.py`.

## 4) Primary data and control flows

### 4.1 Scientific review lifecycle
1. User contributes/updates a georeferenced point.
2. Scientific inference endpoint computes prediction candidates and confidence.
3. Point enters review queue when human validation is needed.
4. Reviewer/admin validates through protected scientific endpoints.
5. Decision and transition events are persisted to validation history models.
6. Dashboard and prioritization services aggregate operational/scientific indicators.

### 4.2 Enrichment lifecycle
1. A plant/point is submitted to enrichment endpoints.
2. Pipeline queries taxonomic and biodiversity providers.
3. Normalization and confidence logic consolidates canonical fields.
4. Status and payload summary are persisted with per-source traceability.

### 4.3 Environmental and territorial lifecycle
1. Climate and MapBiomas endpoints pull or synchronize external context.
2. Alerts and contextual data are exposed to admin/analysis workflows.
3. Territorial prioritization consumes climate + validation density + recency features.

### 4.4 Mobile parity lifecycle
1. Mobile consumes canonical API base from `EXPO_PUBLIC_API_URL`.
2. Mobile parity endpoints deliver normalized map previews and offline metadata/download payloads.
3. Shared identification pipeline preserves contract parity between web and mobile.

## 5) Human review and governance controls

- Review-sensitive endpoints use reviewer/admin checks (`IsReviewerOrAdmin` and role/group checks).
- AI output is assistive; final scientific decision is explicitly human.
- Validation history models provide traceability/auditability for lifecycle transitions.
- Integration health services expose operational visibility for third-party dependencies.

## 6) Testing and architectural verification

Current automated tests validate key architecture contracts:
- scientific risk/prioritization logic,
- reviewer permission boundaries,
- enrichment pipeline behavior and partial-failure handling,
- integration health/status classification,
- climate and environmental services,
- mapbiomas and identification-related scenarios.

## 7) Current architectural constraints

- The `mapping` app still concentrates multiple bounded contexts.
- Legacy and modern endpoint families coexist under the same project namespace.
- Some integrations are optional and environment-sensitive (keys/network/timeouts).

These constraints are currently mitigated through service/domain separation and explicit operational health endpoints.
