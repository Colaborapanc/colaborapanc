# API

## Scope

This canonical API guide describes ColaboraPANC's active HTTP surface for backend, web frontend, mobile app, integrations, and operational/admin workflows.

**Source of truth for routing:** `mapping/urls.py` (loaded by `config/urls.py`).

## 1) Base URL, composition, and conventions

- Local base URL: `http://localhost:8000`
- Route composition:
  - `config/urls.py` includes `mapping.urls` at root.
  - API and web routes coexist in the same URL tree.
- Web account routes (django-allauth): `/accounts/*`
- Platform healthcheck: `GET /healthz/`

### Authentication model

- Token/session login: `POST /api/token/login/`
- Account creation: `POST /api/register/`
- Most API resources require `IsAuthenticated`.
- Scientific review routes require reviewer/admin permission.
- Some operational endpoints require staff/superuser.

### Maturity tags used below

- **Stable**: central route with active code path and established contract.
- **Legacy-compatible**: kept for compatibility while newer surfaces coexist.
- **Operational/Admin**: admin/observability/support usage.
- **Evolving**: active domain, contract still maturing.

## 2) Endpoint groups by functional domain

## 2.1 Identity and account domain

| Endpoint | Method | Auth | Purpose | Main input | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/token/login/` | POST | AllowAny | Token login + session | `username` or `email`, `password` | `token`, `user_id`, `username` | Stable |
| `/api/register/` | POST | AllowAny | Create account and token | `nome`, `email`, `password` | `token`, `user_id`, `username` | Stable |
| `/api/user/profile/` | GET | Authenticated | Current user profile summary | – | user profile + stats | Stable |
| `/api/user/change-password/` | POST | Authenticated | Change password and rotate token | `senha_atual`, `nova_senha` | success detail + new token | Stable |
| `/accounts/*` | GET/POST | Session/Web | allauth web account management | allauth forms | HTML/account flow | Stable |

## 2.2 Points, contribution, and core data domain

### Resource endpoints

| Endpoint | Method(s) | Auth | Purpose | Main params/body | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/pontos/` | GET, POST | Mixed (create typically authenticated) | List/create georeferenced points | `nome_popular`, `localizacao`, optional scientific/food fields | serialized `PontoPANC` | Stable |
| `/api/pontos/<id>/` | GET, PUT, PATCH, DELETE | Auth-sensitive | Retrieve/update/delete point | point payload fields | serialized point / status | Stable |
| `/api/pontos/<id>/enriquecimento/` | POST | Authenticated | Trigger enrichment for one point | optional enrichment context | enrichment result payload | Stable |
| `/api/pontos/<id>/revalidar/` | POST | Authenticated | Trigger revalidation for one point | – | revalidation result payload | Stable |
| `/api/pontos/revalidar-lote/` | POST | Authenticated/Admin usage | Batch revalidation | `ids` (optional), `limite` | batch summary/results | Operational/Admin |
| `/api/compartilhamentos/` | GET, POST, ... | Auth | Share/collaboration resource | model fields | DRF resource payload | Stable |

### Supporting search/utilities

| Endpoint | Method | Auth | Purpose | Main params | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/busca-avancada/` | GET | AllowAny | Filtered point search | name/location/status/bbox filters | filtered point list | Stable |
| `/api/plantas/` | GET | AllowAny | Reference plants listing | `nome`, `bioma`, `origem` | plant list | Stable |
| `/api/autocomplete-nome/` | GET | AllowAny | Popular name suggestions | `term` (+ optional detailed mode) | suggestion list | Legacy-compatible + Stable |
| `/api/nome-cientifico/` | GET | AllowAny | Resolve scientific name | `nome_popular` | resolution payload | Legacy-compatible + Stable |
| `/api/geocode/` | POST | AllowAny | Reverse geocode utility | location payload | geocode result | Legacy-compatible |

## 2.3 Scientific review and validation domain (`/api/cientifico/*`)

| Endpoint | Method | Auth | Purpose | Main params/body | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/cientifico/pontos/<ponto_id>/inferencia/` | POST | Authenticated | Run AI inference from point image | optional `X-PLANTID-KEY` header | `PredicaoIA` record payload | Stable |
| `/api/cientifico/revisao/fila/` | GET | Reviewer/Admin | Review queue listing | `confianca`, `status_fluxo`, `dias` | filtered points in review states | Stable |
| `/api/cientifico/revisao/pontos/<ponto_id>/` | GET | Reviewer/Admin | Review detail for one point | `ponto_id` | point + last prediction + last validation + history | Stable |
| `/api/cientifico/pontos/<ponto_id>/validacao/` | POST | Reviewer/Admin | Human validation decision | `decisao_final`, optional comments/species | `ValidacaoEspecialista` payload | Stable |
| `/api/cientifico/pontos/<ponto_id>/historico/` | GET | Reviewer/Admin | Scientific decision/event history | `ponto_id` | validation history list | Stable |
| `/api/cientifico/dashboard/` | GET | Authenticated | Scientific analytics summary | – | metrics/distributions/prioritization sample | Stable |

## 2.4 Communication, notifications, preferences, and routes domain

### DRF router resources (primary)

| Endpoint | Method(s) | Auth | Purpose | Main input | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/notificacoes/` | GET, POST, PATCH... + actions | Authenticated | User notifications | notification/action payload | notifications and action results | Stable |
| `/api/dispositivos-push/` | GET, POST, PATCH... | Authenticated | Push device token lifecycle | `token`, `plataforma` | device registration payload | Stable |
| `/api/conversas/` | GET, POST, ... | Authenticated | Conversation lifecycle | participant identifiers | conversation payload | Stable |
| `/api/mensagens/` | GET, POST, ... | Authenticated | Message lifecycle | `conversa_id`, `conteudo` | message payload | Stable |
| `/api/preferencias/` | GET, POST, PATCH | Authenticated | User preferences | preference fields | preference payload | Stable |
| `/api/recomendacoes/` | GET (+ action) | Authenticated | Personalized recommendations | recommendation action payload | recommendation list/payload | Stable |
| `/api/rotas/` | GET, POST, PATCH... | Authenticated | Route planning records | route fields | route payload | Stable |

### Companion compatibility endpoints (`views.py`)

| Endpoint | Method | Auth | Purpose | Maturity |
|---|---|---|---|---|
| `/api/push-token/` | POST | Mixed | Legacy push registration flow | Legacy-compatible |
| `/api/notificacoes/` | GET | Mixed | Legacy notifications listing | Legacy-compatible |
| `/api/conversas/` | GET | Mixed | Legacy conversations listing | Legacy-compatible |
| `/api/mensagens/` | GET | Mixed | Legacy messages listing | Legacy-compatible |
| `/api/compartilhamentos/` | POST | Mixed | Legacy sharing flow | Legacy-compatible |

## 2.5 AR and advanced identification domain

| Endpoint | Method(s) | Auth | Purpose | Main input | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/identificar-planta/` | POST | AllowAny/Auth (context-dependent) | Advanced image identification flow | image + options | identification payload | Evolving |
| `/api/buscar-plantas/` | GET | AllowAny | Search plants in advanced flow | query terms | search results | Evolving |
| `/api/modelos-ar-disponiveis/` | GET | AllowAny | Public AR models catalog | optional filters | AR model list | Evolving |
| `/api/plantas-customizadas/` | CRUD | Auth | Custom plants resource | model fields | DRF resource payload | Evolving |
| `/api/modelos-ar/` | CRUD | Auth | AR models resource | model fields | DRF resource payload | Evolving |
| `/api/historico-identificacao/` | GET | Auth | Identification history | optional filters | historical records | Evolving |
| `/api/referencias-ar/` | CRUD | Auth | AR references resource | model fields | DRF resource payload | Legacy-compatible/Evolving |

## 2.6 Offline species and mobile parity domain

### Offline species inventory/download APIs

| Endpoint | Method(s) | Auth | Purpose | Main params/body | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/especies-referenciais/busca/` | GET | AllowAny/Auth | Canonical species search | query terms | normalized species list | Stable |
| `/api/especies-referenciais/busca-recursiva/` | GET | AllowAny/Auth | Extended species recursive search | query terms | expanded result set | Evolving |
| `/api/plantas-offline/disponiveis/` | GET | Auth | List downloadable plants | filters | availability list | Stable |
| `/api/plantas-offline/pacotes/` | GET | Auth | List predefined offline packs | – | pack list | Stable |
| `/api/plantas-offline/pacotes/<pacote_id>/baixar/` | POST | Auth | Download predefined pack | `pacote_id` | package payload | Stable |
| `/api/plantas-offline/baixar/` | POST | Auth | Download selected plants | selection payload | selected species payload | Stable |
| `/api/plantas-offline/<planta_id>/dados/` | GET | Auth | Get one offline plant payload | `planta_id` | plant payload | Stable |
| `/api/plantas-offline/minhas/` | GET | Auth | User offline downloaded list | – | user list | Stable |
| `/api/plantas-offline/<planta_id>/remover/` | POST | Auth | Remove one downloaded plant | `planta_id` | status payload | Stable |
| `/api/plantas-offline/configuracoes/` | GET, POST | Auth | Offline settings read/update | settings payload | settings payload | Stable |
| `/api/plantas-offline/sincronizar/` | POST | Auth | Offline status sync | sync payload | sync summary | Stable |

### Mobile parity APIs (`/api/mobile/*`)

| Endpoint | Method | Auth | Purpose | Main params/body | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/mobile/identificacao/imagem/` | POST | Authenticated | Canonical mobile image-identification contract | multipart image (`imagem`/`foto`), optional toggles | normalized identification payload | Stable |
| `/api/mobile/mapa/previews/` | GET | Authenticated | Canonical map-preview payload for mobile | `q`, `limite` | `{total, resultados[]}` | Stable |
| `/api/mobile/offline/base/metadata/` | GET | Authenticated | Offline base version metadata | – | version/count metadata | Stable |
| `/api/mobile/offline/base/` | GET | Authenticated | Offline base export payload | `limite`, `busca` | metadata + species payload | Stable |

## 2.7 Environmental and territorial domain

### MapBiomas endpoints

| Endpoint | Method | Auth | Purpose | Expected return | Maturity |
|---|---|---|---|---|---|
| `/api/mapbiomas/alertas/` | GET | AllowAny/Auth | deforestation alerts query | alerts payload | Stable/Evolving |
| `/api/mapbiomas/alertas/<alert_code>/` | GET | AllowAny/Auth | alert detail by code | alert detail payload | Stable/Evolving |
| `/api/mapbiomas/territorios/` | GET | AllowAny/Auth | territory lookup | territory payload | Stable/Evolving |
| `/api/mapbiomas/propriedade/` | GET | AllowAny/Auth | CAR/property-focused lookup | property alerts payload | Stable/Evolving |
| `/api/mapbiomas/ponto/` | GET | AllowAny/Auth | point contextual lookup | contextual payload | Stable/Evolving |
| `/api/mapbiomas/pontos-panc/<ponto_id>/` | GET | AllowAny/Auth | nearby alerts for point | point-alert payload | Stable/Evolving |
| `/api/mapbiomas/testar/` | GET | AllowAny/Auth | connectivity/health probing | test status payload | Operational/Admin-like |

### Climate endpoints

| Endpoint | Method | Auth | Purpose | Main params/body | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/alertas-ativos/` | GET | AllowAny | Active climate alerts | `ponto_id`, `limit` | `{count, results[]}` | Stable |
| `/api/historico_alertas_api/` | GET | AllowAny | Climate alerts history | `ponto_id`/`ponto`, `limit` | `{count, results[]}` | Stable |
| `/api/clima/sincronizar/` | POST | Staff/Superuser | Trigger climate sync | optional `ponto_id`, `only_active` | created/updated/skipped/errors summary | Operational/Admin |
| `/api/clima/status/` | GET | Staff/Superuser | Climate/environment operational status | – | integrations + alert metrics | Operational/Admin |

## 2.8 Taxonomic enrichment domain (`/api/enriquecimento/*`)

| Endpoint | Method | Auth | Purpose | Main params/body | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/enriquecimento/` | POST | AllowAny | Enrich scientific name and optional linked plant | `nome_cientifico`, optional `planta_id` | enrichment result payload | Stable |
| `/api/enriquecimento/revalidar/` | POST | Authenticated | Re-run enrichment for existing plant | `planta_id` | revalidation result payload | Stable |
| `/api/enriquecimento/<planta_id>/` | GET | AllowAny | Get enriched payload for one plant | `planta_id` | enriched plant payload | Stable |
| `/api/enriquecimento/<planta_id>/historico/` | GET | AllowAny | Get enrichment history | `planta_id` | history list | Stable |

## 2.9 Integration administration and operations domain

| Endpoint | Method | Auth | Purpose | Main params/body | Expected return | Maturity |
|---|---|---|---|---|---|---|
| `/api/admin/integracoes/health/` | GET | Auth + admin check | Consolidated integration status | – | integrations list/status | Operational/Admin |
| `/api/admin/integracoes/testar/` | POST | Auth + admin check | Run integration probe(s) | optional `integration_name` | execution summary + results[] | Operational/Admin |
| `/painel-admin/integracoes/` | GET/POST | Admin web access | Operational integration panel | optional integration selector | HTML dashboard | Operational/Admin |

## 3) Legacy/experimental watchlist

Treat these as compatibility or partially mature surfaces:

- coexistence of router resources and function-based compatibility endpoints in communication namespace,
- `/api/identificar/` legacy hybrid flow coexisting with scientific and advanced identification contracts,
- AR/customization and recursive species search flows marked as evolving,
- mixed web/API route tree that includes operational admin pages.

## 4) Standard response and error expectations

- `200/201`: successful operation.
- `400`: validation/business rule failure.
- `401/403`: authentication/authorization failure.
- `404`: resource not found.
- `503`: upstream integration unavailable (notably inference providers).

## 5) Suggested technical annex (recommended)

To avoid overloading this canonical guide while preserving complete route inventory, maintain dedicated inventory annexes, for example:

- `docs/en/api-endpoint-inventory.md`
- `docs/pt-BR/api-inventario-endpoints.md`

Recommended annex structure:
- exhaustive endpoint list,
- request/response schemas per route,
- serializer/service reference map,
- maturity and compatibility lifecycle tags,
- deprecation notes and migration path.
