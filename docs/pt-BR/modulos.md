# Módulos

## Escopo

Este mapa canônico de módulos documenta a organização funcional atual nas camadas de backend, mobile e testes.

## 1) Módulos de backend por domínio (`mapping/`)

### 1.1 Plataforma, roteamento e superfície web/API
- `mapping/urls.py`: composição de rotas para páginas web, ferramentas admin, routers REST, APIs científicas, clima, mapbiomas, enriquecimento, paridade mobile e endpoints offline.
- `mapping/views.py`: páginas web + endpoints mistos legados/operacionais.
- `mapping/views_api.py`: APIs REST/científicas (fila de revisão, inferência, validação, dashboard, viewsets de comunicação/recursos).
- Views especializadas:
  - `mapping/views_ar_identificacao.py`
  - `mapping/views_offline_plantas.py`
  - `mapping/views_mapbiomas.py`
  - `mapping/views_climate.py`
  - `mapping/views_enrichment.py`
  - `mapping/views_mobile_parity.py`

### 1.2 Domínio científico e botânico central
- Modelos:
  - `PontoPANC` (ciclo da observação georreferenciada)
  - `PlantaReferencial` (base canônica de espécies)
  - `PredicaoIA`, `ValidacaoEspecialista`, `HistoricoValidacao`
  - entidades de histórico de enriquecimento (`HistoricoEnriquecimento`, `EnriquecimentoTaxonomicoHistorico`)
- Serviços:
  - `mapping/services/ia_identificacao.py` + `mapping/services/ia_identificacao/*`
  - `mapping/services/plant_identification_service.py`
  - `mapping/services/enrichment/*`

### 1.3 Domínio ambiental e territorial
- APIs e sincronização ambiental:
  - `mapping/views_mapbiomas.py`, `mapping/views_climate.py`
  - `mapping/services/mapbiomas_service.py`, `mapping/services/mapbiomas_alert_service.py`
  - `mapping/services/weather/inmet.py`, `mapping/services/weather/open_meteo.py`
  - `mapping/services/nasa_firms_service.py`
- Priorização territorial:
  - engine de domínio `mapping/domains/territorial/prioritization.py`
  - facade de compatibilidade `mapping/services/priorizacao_territorial.py`

### 1.4 Domínio de colaboração, comunicação e comunidade
- Modelos/endpoints de comunicação:
  - `Notificacao`, `DispositivoPush`, `Conversa`, `Mensagem`
  - viewsets relacionados em `views_api.py` e `views.py`
- Comunidade/gamificação:
  - `Badge`, `Missao`, `MissaoUsuario`, `PontuacaoUsuario`, `RankingRevisor`, `Grupo`, `Evento`
  - fluxos de missão/ranking/admin em `views.py`

### 1.5 Domínio de rotas, recomendação, compartilhamento e comércio
- Rotas e roteiros:
  - `Rota`, `RotaPonto`, `RoteiroPANC`, `RoteiroPANCItem`
  - cálculo de rotas em `mapping/services/rotas_service.py`
- Recomendação e compartilhamento:
  - `RecomendacaoPANC`, `CompartilhamentoSocial`
  - lógica de recomendação em `mapping/services/recomendacao_ml.py`
- Entidades de comércio externo:
  - `IntegracaoEcommerce`, `ProdutoSemente`, `LojaExterno`, `ProdutoExterno`

### 1.6 Domínio de AR, offline e paridade mobile
- Entidades e endpoints de AR:
  - `PlantaCustomizada`, `ModeloAR`, `HistoricoIdentificacao`, `ReferenciaAR`
  - `mapping/views_ar_identificacao.py`
- Entidades e endpoints offline:
  - `PacotePlantasOffline`, `PlantaOfflineUsuario`, `ConfiguracaoOffline`, `CacheOffline`
  - `mapping/views_offline_plantas.py`
- Contrato de paridade mobile:
  - `mapping/services/mobile_parity_service.py`
  - `mapping/views_mobile_parity.py`

### 1.7 Observabilidade de integrações e ferramental operacional
- Saúde e sondas de integração:
  - `mapping/services/integrations/healthcheck.py`
  - `mapping/services/integration_health.py`
  - endpoints de health para admin em `views.py`
- Comandos de gestão em `mapping/management/commands/` para sync/import/backfill/auditoria.

## 2) Módulos transversais de backend

- `mapping/serializers.py`: DTOs e normalização de payload para APIs.
- `mapping/permissions.py`: fronteira de permissão para revisor/admin.
- `mapping/signals.py`: comportamento orientado a eventos (ex.: progressão de gamificação).
- `mapping/forms.py` e templates para fluxos web de formulário/UI.

## 3) Módulos mobile (`mobile/src/`)

### 3.1 Camada de API e comunicação
- `mobile/src/config/api.js`: registro canônico de endpoints mobile e resolução de URL base.
- Serviços HTTP/auth e comunicação:
  - `httpClient.js`, `apiClient.js`, `authService.js`, `comunicacaoService.js`, `mensagensService.js`, `notificacoesService.js`.

### 3.2 Serviços de funcionalidades
- Serviços botânicos/científicos:
  - `identificacaoService.js`, `aiAssistService.js`, `enrichmentService.js`, `enriquecimentoService.js`.
- Serviços de offline/sync:
  - `offlineService.js`, `offlineStorage.js`, `plantasOfflineService.js`, `speciesFocusService.js`, `autoDetectionService.js`.
- Rotas/compartilhamento e utilitários:
  - `rotasService.js`, `compartilhamentoService.js`, `droneMissionService.js`, `i18nService.js`.

### 3.3 Módulos de UI/telas
- Telas centrais: mapa, cadastro, detalhe de contribuição, revisão, identificação, notificações, perfil, plantas/configuração offline.
- As telas estão em `mobile/src/screens/` e consomem serviços como fronteira primária de integração com backend.

## 4) Módulos de teste (`tests/`)

A suíte atual está organizada por domínios de comportamento/contrato:
- núcleo científico e provedores de IA,
- permissões,
- pipeline de enriquecimento e enriquecimento via wikipedia,
- health de integrações e utilitários de status,
- alertas climáticos/ambientais,
- integração mapbiomas,
- domínio de priorização territorial,
- fluxo de cadastro/autocomplete de pontos.

## 5) Resumo de interação entre domínios

1. Views recebem requisições HTTP e acionam serializers/serviços.
2. Módulos de serviço/domínio executam regras de negócio, integrações e normalização.
3. Modelos persistem estado de ciclo de vida e artefatos de auditoria.
4. Mobile consome contratos estáveis de API e endpoints de paridade.
5. Testes validam contratos transversais críticos e caminhos sensíveis a regressão.
