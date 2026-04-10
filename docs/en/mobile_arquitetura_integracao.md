# Technical evolution of the mobile app with full web compatibility

## 1) Diagnosis of the current architecture

Main incompatibilities identified between mobile and web:

1. **Inconsistent API Agreement**
   - Mobile endpoint pointed to `cadastrar_ponto_api/` (not found in current URLs).
   - `offlineService` used `api.get()`/`api.post()` without a real HTTP client.
   - Divergent `localizacao` formats (`[lng,lat]` in the app vs GeoJSON in part of the API).

2. **Incomplete and non-resilient offline**
   - Previous cache was only in memory (`offlineStorage` lost data when closing the app).
   - There was no persistent queue with deduplication, retries and operational log.

3. **Navigation with broken routes**
   - Home called `Alertas`/`Profile`, but stack exposed other routes.

4. **Missing strategic modules**
   - Local base of focus species without uniform structure for filter and priority.
   - No auditable AI inference trail for human review.
   - No modular model for ingesting missions/drone batches.

## 2) Secure implementation strategy (without breaking the existing one)

1. Create **integration base layer** (HTTP + storage + sync) without removing current screens.
2. Standardize mobile payloads to the **existing web agreement**.
3. Introduce advanced features such as **decoupled modules** (AI, focus species, drone).
4. Keep old behavior compatible, but with persistent offline fallback.

## 3) Implementation delivered at this stage

### 3.1 Data layer and API
- `mobile/src/config/api.js`
  - centralizes base URL and real endpoints of the current backend.
  - corrects registration route for `/api/pontos/`.
- `mobile/src/services/httpClient.js`
  - unified HTTP client with optional token and `credentials: include`.

### 3.2 Real offline + synchronization
- `mobile/src/services/offlineStorage.js`
  - persistence with `AsyncStorage` for cache, queue, logs, AI history and missions.
  - coordinate normalization and queue deduplication by idempotent key.
- `mobile/src/services/offlineService.js`
  - online/offline registration with automatic fallback.
  - resilient synchronization with retry and logs.
  - incremental reference synchronization via `/api/offline-sync/`.

### 3.3 Field flow and operational UX
- `mobile/src/screens/CadastroPontoScreen.js`
  - registration works online/offline, with local queuing.
  - Offline AI suggestion button for pre-filling.
- `mobile/src/screens/MapScreen.js`
  - search via offline layer and supports array/GeoJSON location.
- `mobile/src/screens/HomeScreen.js`
  - clear indicator of online/offline status and pending issues.
- `mobile/App.js`
  - active automatic synchronization and routes aligned with the screens.

### 3.4 Focus species + AI + drone (structural basis)
- `mobile/src/services/speciesFocusService.js`
  - local base of focus species with required fields and filters.
- `mobile/src/services/aiAssistService.js`
  - auditable offline inference (model version, confidence, coordinate, image, human review).
- `mobile/src/services/droneMissionService.js`
  - initial model for mission and georeferenced capture batch.

## 4) Recommended order for continuity

1. Validate mobile authentication with (token/sessão) backend and establish a single contract.
2. Connect focus species management screen to `speciesFocusService`.
3. Integrate human review of AI inferences into the scientific flow (`/api/cientifico/*`).
4. Create drone missions/lots screen using `droneMissionService`.
5. Add automated sync/offline tests (unit + integration).

## 5) Be careful not to break the web

- Do not change central models in the backend without versioned migration.
- Do not change canonical field names (`nome_popular`, `nome_cientifico`, `status_validacao`, `localizacao`).
- Avoid duplicating validation rules that already exist in the backend; in the app use light pre-validation.
- Maintain AI traceability always pending human review by default.

## 6) Recommended functional tests

### Online tests
- Login and map loading (`/api/pontos/`).
- Point registration with geolocation and image.
- Synchronization of references (`/api/offline-sync/`).

### Offline tests
- Create 3 registrations in airplane mode.
- Close and reopen app (pending data must persist).
- Return connection and validate queue emptying.
- Check sync logs and absence of duplication.

### Assisted AI Testing
- Generate suggestion based on loaded location.
- Check recording in history with `model_version`, trust and review status.

### Drone preparation tests
- Register mission + batch with images/points.
- Validate local persistence and pending status.

## 7) New functionality: offline targeted species base + automatic detection

### Components added/adjusted
- `mobile/src/services/speciesFocusService.js`
  - searches for species available in existing integrations (`/api/plantas-offline/disponiveis/`)
  - saves manual species selection
  - estimates package offline
  - generates local offline database with metadata, version and integrity hash
- `mobile/src/services/autoDetectionService.js`
  - uses offline base + local heuristic AI for assisted/automatic detection
  - applies anti-duplicity cooldown
  - capture geolocation
  - creates automatic registration in offline/online flow with status pending review
  - automatically marks point in map cache
- `mobile/src/services/offlineStorage.js`
  - new blocks for base metadata (`SPECIES_BASE_META`) and detection history
- `mobile/src/screens/PlantasOfflineScreen.js`
  - starts displaying status of the targeted offline base and generates base after selected download
- `mobile/src/screens/IdentificarPlantaScreen.js`
  - new offline auto-discovery flow with trackable record creation

### Compatibility guarantees
- Does not automatically validate registration as definitive scientific
- Maintains record as pending/reviewable
- Reuses existing endpoint and structure for points/sync
- Maintains later synchronization via offline queue
