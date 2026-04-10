# API

## Scope

This canonical API guide documents the active HTTP surface exposed by ColaboraPANC for:

- backend/web clients,
- frontend web,
- mobile app,
- integration and operational tooling.

Authoritative route registry: `mapping/urls.py` (included by `config/urls.py`).

## 1) Base URL and routing model

- Local base URL: `http://localhost:8000`
- Root URL composition:
  - `config/urls.py` includes `mapping.urls` at root.
  - `mapping/urls.py` mixes web routes and API routes.
- Account/auth web flow (allauth): `/accounts/*`
- Health endpoint: `GET /healthz/`

## 2) Authentication and authorization model

### 2.1 Main auth flows
- `POST /api/token/login/`
  - Purpose: obtain DRF token and login session.
  - Body: `username|email`, `password`.
  - Returns: `token`, `user_id`, `username`.
- `POST /api/register/`
  - Purpose: create account + issue token.
  - Body: `nome`, `email`, `password`.
  - Returns: `token`, `user_id`, `username`.

### 2.2 User profile/authenticated account
- `GET /api/user/profile/`
- `POST /api/user/change-password/`

### 2.3 Permission tiers used by API
- **Public (`AllowAny`)**: selected read/search and enrichment entrypoints.
- **Authenticated (`IsAuthenticated`)**: most operational endpoints.
- **Reviewer/Admin (`IsReviewerOrAdmin`)**: scientific review/validation endpoints.
- **Staff/Superuser**: climate sync/status and integration admin testing endpoints.

## 3) Endpoint maturity legend

- **Stable**: core route with active usage and explicit service/serializer backing.
- **Legacy-compatible**: route kept for compatibility while newer contracts coexist.
- **Operational/Admin**: endpoints intended for admin, observability, and support workflows.
- **Evolving**: route family under active evolution (contract may still mature).

## 4) Functional endpoint groups

## 4.1 Core points and contribution domain

### Router/resource endpoints (`/api/` via DRF)
- `/api/pontos/` (**Stable**, auth-sensitive create/update usage)
  - Purpose: list/create/update georeferenced PANC points.
  - Main create fields:
    - naming: `nome_popular`, optional scientific names/variants,
    - geodata: `localizacao` (`[lng,lat]` or object), optional `latitude`/`longitude`,
    - optional manual edible/seasonality fields,
    - `enriquecer_automaticamente` toggle.
  - Returns: serialized `PontoPANC` with lifecycle/enrichment fields.
- `/api/pontos/<id>/enriquecimento/` (**Stable**, action)
- `/api/pontos/<id>/revalidar/` (**Stable**, action)
- `/api/pontos/revalidar-lote/` (**Operational/Admin-like batch action)
- `/api/compartilhamentos/` (**Stable**, collaboration resource)

### Supporting search/name routes
- `GET /api/busca-avancada/` (**Stable**)
- `GET /api/plantas/` (**Stable**)
- `GET /api/autocomplete-nome/` (**Legacy-compatible + Stable**)
- `GET /api/nome-cientifico/` (**Legacy-compatible + Stable**)
- `POST /api/geocode/` (**Legacy-compatible utility**)

## 4.2 Scientific workflow domain (`/api/cientifico/*`)

- `POST /api/cientifico/pontos/<ponto_id>/inferencia/` (**Stable**, authenticated)
  - Purpose: run AI inference for an existing point image.
  - Main behavior:
    - validates point/image,
    - calls multi-provider IA service,
    - persists `PredicaoIA`, updates point status/score,
    - appends validation history event.
  - Optional header: `X-PLANTID-KEY`.
  - Returns: `PredicaoIA` payload.
- `GET /api/cientifico/revisao/fila/` (**Stable**, reviewer/admin)
  - Query filters: `confianca`, `status_fluxo`, `dias`.
- `GET /api/cientifico/revisao/pontos/<ponto_id>/` (**Stable**, reviewer/admin)
  - Returns: point, latest prediction, latest validation, history.
- `POST /api/cientifico/pontos/<ponto_id>/validacao/` (**Stable**, reviewer/admin)
  - Body: `decisao_final` (`validado|rejeitado|necessita_revisao`), optional `especie_final`, `motivo_divergencia`, `observacao`.
  - Returns: `ValidacaoEspecialista` record.
- `GET /api/cientifico/pontos/<ponto_id>/historico/` (**Stable**, reviewer/admin)
- `GET /api/cientifico/dashboard/` (**Stable**, authenticated analytics)

## 4.3 Communication, preferences, and social domain

### Router resources (`views_api.py`)
- `/api/notificacoes/` (**Stable**)
  - Includes custom actions like non-read listing and mark-as-read.
- `/api/dispositivos-push/` (**Stable**)
- `/api/conversas/` (**Stable**)
- `/api/mensagens/` (**Stable**)
- `/api/preferencias/` (**Stable**)
- `/api/recomendacoes/` (**Stable**, read-oriented)
- `/api/rotas/` (**Stable**)

### Legacy-compatible companion endpoints (`views.py`)
- `POST /api/push-token/`
- `GET /api/notificacoes/`
- `GET /api/conversas/`
- `GET /api/mensagens/`
- `POST /api/compartilhamentos/`

> Note: router and legacy endpoints coexist in this domain and should be treated as compatibility surface.

## 4.4 AR and advanced identification domain

- `POST /api/identificar-planta/` (**Evolving**)
- `GET /api/buscar-plantas/` (**Evolving**)
- `GET /api/modelos-ar-disponiveis/` (**Evolving**)
- `/api/plantas-customizadas/` (DRF resource, **Evolving**)
- `/api/modelos-ar/` (DRF resource, **Evolving**)
- `/api/historico-identificacao/` (read-oriented resource, **Evolving**)
- `/api/referencias-ar/` (router resource from `views.py`, **Legacy-compatible/Evolving**)

## 4.5 Offline species and mobile parity domain

### Offline species APIs
- `GET /api/especies-referenciais/busca/` (**Stable**)
- `GET /api/especies-referenciais/busca-recursiva/` (**Evolving**)
- `GET /api/plantas-offline/disponiveis/` (**Stable**)
- `GET /api/plantas-offline/pacotes/` (**Stable**)
- `POST /api/plantas-offline/pacotes/<pacote_id>/baixar/` (**Stable**)
- `POST /api/plantas-offline/baixar/` (**Stable**)
- `GET /api/plantas-offline/<planta_id>/dados/` (**Stable**)
- `GET /api/plantas-offline/minhas/` (**Stable**)
- `POST /api/plantas-offline/<planta_id>/remover/` (**Stable**)
- `GET|POST /api/plantas-offline/configuracoes/` (**Stable**)
- `POST /api/plantas-offline/sincronizar/` (**Stable**)

### Mobile parity APIs (`/api/mobile/*`)
- `POST /api/mobile/identificacao/imagem/` (**Stable**, authenticated)
  - Input: multipart image (`imagem` or `foto`), optional `usar_custom_db`, `usar_google`.
  - Returns: normalized identification payload (`sucesso`, species names, score, review pending flag, candidate metadata).
- `GET /api/mobile/mapa/previews/` (**Stable**, authenticated)
  - Query: `q`, `limite`.
  - Returns: lightweight map cards for mobile rendering.
- `GET /api/mobile/offline/base/metadata/` (**Stable**, authenticated)
- `GET /api/mobile/offline/base/` (**Stable**, authenticated)
  - Query: `limite`, `busca`.

## 4.6 Environmental and territorial domain

### MapBiomas APIs (`/api/mapbiomas/*`)
- `GET /api/mapbiomas/alertas/`
- `GET /api/mapbiomas/alertas/<alert_code>/`
- `GET /api/mapbiomas/territorios/`
- `GET /api/mapbiomas/propriedade/`
- `GET /api/mapbiomas/ponto/`
- `GET /api/mapbiomas/pontos-panc/<ponto_id>/`
- `GET /api/mapbiomas/testar/`

Status: **Stable/Evolving** (integration-dependent responses).

### Climate APIs
- `GET /api/alertas-ativos/` (**Stable**, public read)
  - Query: `ponto_id`, `limit`.
- `GET /api/historico_alertas_api/` (**Stable**, public read)
  - Query: `ponto_id|ponto`, `limit`.
- `POST /api/clima/sincronizar/` (**Operational/Admin**, staff/superuser)
  - Body: optional `ponto_id`, `only_active`.
- `GET /api/clima/status/` (**Operational/Admin**, staff/superuser)

## 4.7 Taxonomic enrichment domain (`/api/enriquecimento/*`)

- `POST /api/enriquecimento/` (**Stable**, public entrypoint)
  - Body: `nome_cientifico`, optional `planta_id`.
- `POST /api/enriquecimento/revalidar/` (**Stable**, authenticated)
  - Body: `planta_id`.
- `GET /api/enriquecimento/<planta_id>/` (**Stable**)
- `GET /api/enriquecimento/<planta_id>/historico/` (**Stable**)

## 4.8 Integrations/admin and operational endpoints

- `GET /api/admin/integracoes/health/` (**Operational/Admin**)
- `POST /api/admin/integracoes/testar/` (**Operational/Admin**)
  - Body: optional `integration_name`.
  - Invalid integration name returns `400` with `valid_options`.
- `GET /painel-admin/integracoes/` (**Operational/Admin web panel**)

## 5) Legacy-compatible and mixed-surface endpoints to watch

The following areas intentionally coexist with newer contracts and should be treated as compatibility layer:

- mixed router + function endpoints under similar namespaces (`/api/notificacoes`, `/api/conversas`, `/api/mensagens`, `/api/compartilhamentos`),
- legacy/web hybrid identification route (`/api/identificar/`) alongside scientific and advanced identification APIs,
- web-form/admin routes exposed in same project URL tree as APIs.

## 6) Standard response/error expectations

Common status codes across endpoint families:
- `200/201`: success.
- `400`: validation/business rule failure.
- `401/403`: unauthenticated/unauthorized.
- `404`: resource not found.
- `503`: upstream/integration unavailable (notably in AI inference fallback cases).

## 7) Suggested technical annex (recommended)

To keep this canonical API doc readable while preserving full inventory traceability, maintain a dedicated annex with route-level inventory and contract examples, e.g.:

- `docs/en/api-endpoint-inventory.md`
- `docs/pt-BR/api-inventario-endpoints.md`

Suggested annex contents:
- exhaustive endpoint list,
- per-route request/response schemas,
- serializer references,
- maturity lifecycle tags,
- deprecation/compatibility notes.
