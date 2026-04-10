# Mobile Flows and Advanced Identification Features

## Scope

This canonical technical annex consolidates mobile flow details previously spread across legacy docs (`docs/en/*` and `docs/pt/*`).

It focuses on:
- Expo/React Native mobile architecture,
- image identification,
- human review from mobile-triggered data,
- offline queue and synchronization,
- selective offline packages,
- assistive AI,
- AR and advanced identification resources.

## 1) Mobile architecture (Expo/React Native)

### 1.1 Contract boundary
- Mobile endpoint registry is centralized in `mobile/src/config/api.js`.
- Service layer (`mobile/src/services/*`) is the integration boundary with backend APIs.
- Screens (`mobile/src/screens/*`) should consume services, not raw endpoint URLs.

### 1.2 Core mobile service groups
- **Identification and scientific support:** `identificacaoService.js`, `aiAssistService.js`.
- **Offline and sync:** `offlineService.js`, `offlineStorage.js`, `plantasOfflineService.js`.
- **Advanced capture modules:** `autoDetectionService.js`, `droneMissionService.js`.
- **General API/auth/communication:** `httpClient.js`, `apiClient.js`, `authService.js`, messaging/notifications services.

## 2) Image identification flow

1. User captures/selects image in mobile UI.
2. Mobile sends identification payload to shared identification endpoints.
3. Backend persists prediction context and confidence artifacts.
4. Result is treated as assistive output (not final scientific truth).
5. Point remains reviewable in scientific validation flow.

### Relevant endpoint families
- `POST /api/mobile/identificacao/imagem/`
- `POST /api/cientifico/pontos/<id>/inferencia/`
- `POST /api/identificar-planta/` (advanced/legacy-compatible identification entrypoint)

## 3) Human review in mobile-related lifecycle

- AI output is intentionally **assistive**.
- Final scientific decision is **human validation** via protected scientific endpoints.
- Divergence between AI suggestion and reviewer decision must remain auditable in history models.

Operationally, mobile-created or mobile-enriched records are expected to pass through:
- review queue endpoints,
- reviewer/admin validation endpoints,
- audit/history endpoints.

## 4) Offline registration and synchronization

### 4.1 Offline queue model
- Offline storage persists pending records, sync logs, and local metadata.
- Queue behavior should include idempotency/deduplication and retry-safe sync patterns.
- App restarts must not lose pending offline records.

### 4.2 Sync behavior
- Registration flow supports online-first with offline fallback.
- On reconnect, pending queue is replayed and marked as synced.
- Mobile should expose pending/sync state to users for operational clarity.

## 5) Selective offline packages

### 5.1 What packages are for
Selective packages provide minimal viable species data for field usage with low connectivity.

### 5.2 Typical API surface
- availability list,
- package list,
- package/species download,
- user-downloaded list,
- offline config,
- sync status endpoints.

### 5.3 Compatibility expectations
- Offline package usage must preserve canonical species fields.
- Offline-origin records remain reviewable and must not be auto-promoted to final scientific validation.

## 6) Assistive AI and local heuristics

- Local/mobile AI assistance may prefill or suggest candidate species.
- Confidence context should be recorded when technically available.
- Assistive AI must not bypass reviewer governance.
- Detection automation (when used) should apply anti-duplication safeguards and keep records in reviewable states.

## 7) AR and advanced identification resources

### 7.1 AR capability surface
- AR resources are complementary educational/operational tools.
- 3D model artifacts (where available) should remain optional and non-blocking to core identification flow.

### 7.2 Advanced identification orchestration
- Multi-source identification can combine local/custom and external providers.
- Fallback chains are allowed, but final decision remains human-reviewed.
- Health/credential variability of external providers should be surfaced in admin integration observability.

## 8) Migration and canonical policy

This annex replaces fragmented legacy narrative for mobile/advanced flows. Legacy docs remain as historical technical trace but canonical updates must happen here and in:
- `docs/en/modules.md`
- `docs/en/architecture.md`
- `docs/en/user-guide.md`
