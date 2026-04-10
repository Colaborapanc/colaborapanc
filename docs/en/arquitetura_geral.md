# General architecture of ColaboraPANC

## High level view
The system is composed of:
1. **Django/DRF Backend** (`config/` + `mapping/`).
2. **Geospatial relational database** (PostgreSQL/PostGIS).
3. **Expo/React Native mobile client** (`mobile/`).
4. **External integrations** for botanical AI and environmental data.

##Backend
### Django Core
- Configuration: `config/settings.py`, `config/urls.py`.
- Main URL includes `mapping.urls`.
- Web authentication via `django-allauth` and DRF session (`SessionAuthentication`).

### App `mapping`
- **Models**: PANC mapping, botanical catalogue, scientific validation, gamification, communication, routes, offline, AR.
- **Views**:
  - `views.py`: web routes and legacy endpoints.
  - `views_api.py`: REST APIs and scientific core.
  - `views_offline_plantas.py`, `views_ar_identificacao.py`, `views_mapbiomas.py`.
- **Serialization**: `mapping/serializers.py`.
- **Permissions**: `mapping/permissions.py`.
- **Signs**: `mapping/signals.py` (score and gamification progression).
- **Commands**: `mapping/management/commands/`.

## Database
- Engine configured: `django.contrib.gis.db.backends.postgis`.
- Geographic core entity: `PontoPANC` with `PointField` (`localizacao`) and lat/lon metadata.
- Scientific audit with `PredicaoIA`, `ValidacaoEspecialista`, `HistoricoValidacao`.

## Mobile
- Main app in `mobile/App.js` (stack navigator).
- Integration services in `mobile/src/services/`.
- Central API configuration in `mobile/src/config/api.js` via `EXPO_PUBLIC_API_URL`.
- There is coexistence with `mobile/index.tsx` (expo-router), which requires future standardization.

## Data flow (summary)
1. User registers point (`PontoPANC`) with geolocation and photo.
2. Scientific endpoint performs inference and generates `PredicaoIA`.
3. If necessary, the point enters the review queue.
4. Reviewer validates/rejects and generates `ValidacaoEspecialista`.
5. Event is registered in `HistoricoValidacao`.
6. Dashboard aggregates metrics and territorial prioritization.

## External integrations
- **PlantNet / Plant.id**: botanical identification by image.
- **INMET / Open-Meteo**: weather data/alerts.
- **MapBiomas**: queries for territorial alerts and environmental context.

## Important architectural observations
- The project concentrates many responsibilities in the `mapping` app.
- There are legacy and new endpoints coexisting in the same `/api/` namespace.
- Evolution through domain modularization and explicit API versioning is recommended.
