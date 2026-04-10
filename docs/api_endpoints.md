# Endpoints da API (estado real)

> Base URL local: `http://localhost:8000`

## Autenticação
- `POST /api/token/login/` – login legado por token.
- Rotas de conta web: `/accounts/*` via django-allauth.

## Pontos PANC e busca
- `GET /api/pontos/` (legado em `views.api_pontos`).
- `POST /api/pontos/` (DRF `PontoPANCViewSet.create`) com suporte a:
  - `nome_popular`, `nome_cientifico`, `nome_cientifico_sugerido`, `nome_cientifico_escolhido`
  - `comestibilidade_status`
  - `parte_comestivel_manual` (ou `parte_comestivel`)
  - `frutificacao_manual` (ou `frutificacao_meses`)
  - `colheita_manual` (ou `colheita_periodo`)
  - `localizacao` (array `[lng, lat]` ou GeoJSON-like)
  - `enriquecer_automaticamente` (default: `true`)
- `PUT/PATCH /api/pontos/<id>/` preserva compatibilidade e permite os mesmos campos manuais.
- `GET /api/busca-avancada/` – filtros por nome, cidade, estado, tipo, planta, status e bounding box.
- `GET /api/plantas/` – listagem de plantas referenciais com filtros.
- `GET /api/autocomplete-nome/?term=<texto>` – sugestões rápidas de nome popular (compatível com retorno legado de lista simples).
- `GET /api/autocomplete-nome/?term=<texto>&detailed=1` – sugestões detalhadas com:
  - `nome_popular`
  - `nome_cientifico`
  - `source` (`base_local_validada`, `historico_pontos`, `inaturalist`)
  - `confianca`
- `GET /api/nome-cientifico/?nome_popular=<nome>` – resolve nome científico com fallback seguro e metadados:
  - `nome_cientifico`
  - `source`
  - `resolved` (boolean)

## Núcleo científico de IA
- `POST /api/cientifico/pontos/<id>/inferencia/` (auth).
- `GET /api/cientifico/revisao/fila/` (revisor/admin).
- `GET /api/cientifico/revisao/pontos/<id>/` (revisor/admin).
- `POST /api/cientifico/pontos/<id>/validacao/` (revisor/admin).
- `GET /api/cientifico/pontos/<id>/historico/` (revisor/admin).
- `GET /api/cientifico/dashboard/` (auth).

### Exemplo: validação científica
`POST /api/cientifico/pontos/10/validacao/`
```json
{
  "decisao_final": "validado",
  "especie_final": "Pereskia aculeata",
  "motivo_divergencia": "",
  "observacao": "Confirmação visual em campo"
}
```

## Notificações, mensagens e preferências (router DRF)
- `/api/notificacoes/`
- `/api/dispositivos-push/`
- `/api/conversas/`
- `/api/mensagens/`
- `/api/preferencias/`

## Rotas, recomendações e e-commerce
- `/api/rotas/`
- `/api/recomendacoes/`
- `/api/integracoes-ecommerce/`
- `/api/produtos-semente/`
- `/api/lojas/`
- `/api/produtos/`

## AR e identificação avançada
- `POST /api/identificar-planta/`
- `GET /api/buscar-plantas/`
- `GET /api/modelos-ar-disponiveis/`
- `/api/plantas-customizadas/`
- `/api/modelos-ar/`
- `/api/historico-identificacao/`

## Offline de plantas
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

## Administração de integrações (staff/superuser)
- `GET /api/admin/integracoes/health/` – consulta estado consolidado das integrações.
- `POST /api/admin/integracoes/testar/` – executa teste de uma integração (`integration_name`) ou de todas.

### Exemplo: testar todas integrações
`POST /api/admin/integracoes/testar/`
```json
{}
```

### Exemplo: testar integração específica
`POST /api/admin/integracoes/testar/`
```json
{
  "integration_name": "Open-Meteo"
}
```

### Erro esperado para `integration_name` inválido
`400 Bad Request`
```json
{
  "detail": "integration_name inválido",
  "integration_name": "nome-inexistente",
  "valid_options": ["GBIF", "Global Names Verifier", "INMET"]
}
```

### Campos principais de retorno
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

## Códigos e erros esperados (geral)
- `200/201`: sucesso.
- `400`: payload inválido ou regra de negócio.
- `401/403`: autenticação/permissão insuficiente.
- `404`: recurso inexistente.
- `503`: indisponibilidade de provedor de IA.

## Notas de UX e revisão taxonômica
- A resposta de ponto mantém `status_enriquecimento` para operação interna, mas a UX comum deve priorizar campos práticos (comestível, parte comestível, frutificação e colheita).
- Ambiguidade taxonômica detectada pelo pipeline é registrada em `payload_resumido_validacao.ambiguidade_taxonomica` e pode ativar `validacao_pendente_revisao_humana`.


## Endpoints climáticos (pipeline unificado)

- `GET /api/alertas-ativos/`
  - Query params opcionais: `ponto_id`, `limit`
  - Retorna somente alertas vigentes (inicio <= agora <= fim).
- `GET /api/historico_alertas_api/`
  - Query params opcionais: `ponto`/`ponto_id`, `limit`
  - Retorna histórico completo incluindo status `ativo|expirado`.
- `POST /api/clima/sincronizar/` (admin)
  - Body opcional: `ponto_id`, `only_active`
  - Dispara coleta INMET + Open-Meteo, normaliza e persiste com deduplicação.
- `GET /api/clima/status/` (admin)
  - Retorna status operacional das integrações de Clima/Ambiental e métricas de alertas (total/ativos/expirados).
