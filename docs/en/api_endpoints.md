# API endpoints (real state)

> Base local URL: `http://localhost:8000`

## Authentication
- `POST /api/token/login/` – legacy token login.
- Web account routes: `/accounts/*` via django-allauth.

## PANC points and search
- `GET /api/pontos/` (legacy in `views.api_pontos`).
- `POST /api/pontos/` (DRF `PontoPANCViewSet.create`) with support for:
  - `nome_popular`, `nome_cientifico`, `nome_cientifico_sugerido`, `nome_cientifico_escolhido`
  - `comestibilidade_status`
  - `parte_comestivel_manual` (or `parte_comestivel`)
  - `frutificacao_manual` (or `frutificacao_meses`)
  - `colheita_manual` (or `colheita_periodo`)
  - `localizacao` (`[lng, lat]` or GeoJSON-like array)
  - `enriquecer_automaticamente` (default: `true`)
- `PUT/PATCH /api/pontos/<id>/` preserves compatibility and allows the same manual fields.
- `GET /api/busca-avancada/` – filters by name, city, state, type, plant, status and bounding box.
- `GET /api/plantas/` – list of reference plants with filters.
- `GET /api/autocomplete-nome/?term=<texto>` – quick popular name suggestions (compatible with legacy simple list return).
- `GET /api/autocomplete-nome/?term=<texto>&detailed=1` – detailed suggestions with:
  - `nome_popular`
  - `nome_cientifico`
  - `source` (`base_local_validada`, `historico_pontos`, `inaturalist`)
  - `confianca`
- `GET /api/nome-cientifico/?nome_popular=<nome>` – resolves scientific name with safe fallback and metadata:
  - `nome_cientifico`
  - `source`
  - `resolved` (boolean)

## AI scientific core
- `POST /api/cientifico/pontos/<id>/inferencia/` (auth).
- `GET /api/cientifico/revisao/fila/` (revisor/admin).
- `GET /api/cientifico/revisao/pontos/<id>/` (revisor/admin).
- `POST /api/cientifico/pontos/<id>/validacao/` (revisor/admin).
- `GET /api/cientifico/pontos/<id>/historico/` (revisor/admin).
- `GET /api/cientifico/dashboard/` (auth).

### Example: scientific validation
`POST /api/cientifico/pontos/10/validacao/`
```json
{
  "decisao_final": "validado",
  "especie_final": "Pereskia aculeata",
  "motivo_divergencia": "",
  "observacao": "Confirmação visual em campo"
}
```

## Notifications, messages and preferences (DRF router)
- `/api/notificacoes/`
- `/api/dispositivos-push/`
- `/api/conversas/`
- `/api/mensagens/`
- `/api/preferencias/`

## Routes, recommendations and e-commerce
- `/api/rotas/`
- `/api/recomendacoes/`
- `/api/integracoes-ecommerce/`
- `/api/produtos-semente/`
- `/api/lojas/`
- `/api/produtos/`

## AR and advanced identification
- `POST /api/identificar-planta/`
- `GET /api/buscar-plantas/`
- `GET /api/modelos-ar-disponiveis/`
- `/api/plantas-customizadas/`
- `/api/modelos-ar/`
- `/api/historico-identificacao/`

## Offline of plants
- `GET /api/plantas-offline/disponiveis/`
- `GET /api/plantas-offline/pacotes/`
- `POST /api/plantas-offline/pacotes/<id>/baixar/`
- `POST /api/plantas-offline/baixar/`
- `GET /api/plantas-offline/minhas/`
- `POST /api/plantas-offline/sincronizar/`

## MapBiomas
- `GET /api/mapbiomas/alertas/`
- `GET /api/mapbiomas/alertas/<alert_code>/`
- `GET /api/mapbiomas/territorios/`
- `GET /api/mapbiomas/propriedade/`
- `GET /api/mapbiomas/ponto/`
- `GET /api/mapbiomas/pontos-panc/<id>/`
- `GET /api/mapbiomas/testar/`

## Integration administration (staff/superuser)
- `GET /api/admin/integracoes/health/` – query consolidated status of integrations.
- `POST /api/admin/integracoes/testar/` – performs testing of one integration (`integration_name`) or all of them.

### Example: test all integrations
`POST /api/admin/integracoes/testar/````json
{}
```

### Example: test specific integration
`POST /api/admin/integracoes/testar/````json
{
  "integration_name": "Open-Meteo"
}
```

### Expected error for invalid `integration_name`
`400 Bad Request````json
{
  "detail": "integration_name inválido",
  "integration_name": "nome-inexistente",
  "valid_options": ["GBIF", "Global Names Verifier", "INMET"]
}
```

### Main return fields
- `sucesso`
- `status` / `status_detalhado`
- `tempo_resposta_ms`
- `error_type`
- `mensagem_amigavel`
- `configurada` / `operacional`
- `ultimo_teste_bem_sucedido`
- `ultima_falha_em`
- `ultimo_tipo_problema`
- `latencia_nivel`

## Expected codes and errors (general)
- `200/201`: success.
- `400`: invalid payload or business rule.
- `401/403`: insufficient authentication/permission.
- `404`: non-existent resource.
- `503`: unavailability of AI provider.

## UX notes and taxonomic review
- Point response maintains `status_enriquecimento` for internal operation, but common UX should prioritize practical fields (edible, edible part, fruiting and harvesting).
- Taxonomic ambiguity detected by the pipeline is logged in `payload_resumido_validacao.ambiguidade_taxonomica` and can trigger `validacao_pendente_revisao_humana`.

## Climate endpoints (unified pipeline)

- `GET /api/alertas-ativos/`
  - Optional query params: `ponto_id`, `limit`
  - Returns only current alerts (start <= now <= end).
- `GET /api/historico_alertas_api/`
  - Optional query params: `ponto`/`ponto_id`, `limit`
  - Returns complete history including `ativo|expirado` status.
- `POST /api/clima/sincronizar/` (admin)
  - Optional body: `ponto_id`, `only_active`
  - Triggers INMET + Open-Meteo collection, normalizes and persists with deduplication.
- `GET /api/clima/status/` (admin)
  - Returns operational status of Climate/Environmental integrations and (total/ativos/expirados) alert metrics.
