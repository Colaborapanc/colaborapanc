# Arquitetura

## Escopo

Este documento canônico descreve a arquitetura atual do ColaboraPANC com base no código ativo em:

- `config/*`
- `mapping/models.py`
- `mapping/views*.py`
- `mapping/services/*` e `mapping/domains/*`
- `mapping/urls.py`
- `mobile/src/*`
- `tests/*`

## 1) Visão geral do sistema

O ColaboraPANC está estruturado em quatro camadas conectadas:

1. **Backend web/API (Django + DRF)**
   - Entrada HTTP e composição de rotas em `config/urls.py` e `mapping/urls.py`.
   - Modelos de domínio, views web, endpoints REST e serviços de orquestração em `mapping/`.
2. **Camada de dados geoespaciais (PostgreSQL + PostGIS)**
   - Engine GIS Django configurada com `django.contrib.gis.db.backends.postgis`.
   - Entidade georreferenciada central: `PontoPANC` com ponto geográfico e campos de ciclo de validação.
3. **Cliente mobile (Expo/React Native)**
   - Serviços e telas mobile em `mobile/src/`.
   - Contratos de endpoint centralizados em `mobile/src/config/api.js`.
4. **Camada de integrações externas**
   - Identificação científica (PlantNet/Plant.id).
   - Enriquecimento taxonômico (Global Names, Tropicos, GBIF, iNaturalist, Trefle, Wikimedia).
   - Monitoramento ambiental (MapBiomas, INMET, Open-Meteo, NASA FIRMS).

## 2) Arquitetura do backend

### 2.1 Fronteira de configuração e runtime
- `config/settings.py` controla carga de ambiente, segurança, banco PostGIS, estáticos/mídia, DRF e CORS opcional.
- `config/urls.py` expõe admin, rotas da aplicação, rotas allauth e endpoint operacional `healthz`.

### 2.2 Topologia de URLs e composição de APIs
- `mapping/urls.py` compõe:
  - páginas web e painéis administrativos,
  - viewsets REST por router (`/api/`),
  - endpoints científicos (`/api/cientifico/*`),
  - endpoints ambientais (`/api/mapbiomas/*`, `/api/clima/*`, `/api/alertas-ativos/`),
  - enriquecimento (`/api/enriquecimento/*`),
  - paridade mobile (`/api/mobile/*`),
  - fluxos de espécies offline (`/api/plantas-offline/*`, `/api/especies-referenciais/*`).

### 2.3 Arquitetura de modelos e entidades principais

#### Entidades centrais científicas/geoespaciais
- `PontoPANC`: observação georreferenciada e estado central do ciclo.
- `PlantaReferencial`: catálogo canônico de plantas com campos enriquecidos.
- `PredicaoIA`: payload persistido de predição IA e contexto de confiança.
- `ValidacaoEspecialista`: decisão humana final de validação.
- `HistoricoValidacao`: trilha de auditoria dos eventos do fluxo científico.
- `HistoricoEnriquecimento` e `EnriquecimentoTaxonomicoHistorico`: rastreabilidade das execuções de enriquecimento.

#### Entidades de colaboração e ecossistema
- Comunicação: `Notificacao`, `DispositivoPush`, `Conversa`, `Mensagem`.
- Gamificação/comunidade: `Badge`, `Missao`, `MissaoUsuario`, `PontuacaoUsuario`, `RankingRevisor`, `Grupo`, `Evento`.
- Rotas e compartilhamento: `Rota`, `RotaPonto`, `CompartilhamentoSocial`, `RoteiroPANC`, `RoteiroPANCItem`.
- AR/offline: `PlantaCustomizada`, `ModeloAR`, `ReferenciaAR`, `PacotePlantasOffline`, `PlantaOfflineUsuario`, `ConfiguracaoOffline`, `CacheOffline`.

## 3) Arquitetura de serviços e domínios

### 3.1 Papéis da camada de serviços
- `mapping/services/ia_identificacao*`: orquestração e normalização de provedores de IA.
- `mapping/services/enrichment/*`: pipeline de enriquecimento taxonômico (provedores, confiança, normalização, cache, orquestração).
- `mapping/services/mobile_parity_service.py`: contratos canônicos de payload para paridade web/mobile.
- `mapping/services/integrations/healthcheck.py`: sondas ativas de integração e status operacional.
- `mapping/services/environment*`, `mapbiomas*`, `weather/*`, `nasa_firms_service.py`: ingestão de dados ambientais.

### 3.2 Evolução em nível de domínio
- A lógica de priorização territorial está versionada em `mapping/domains/territorial/prioritization.py`, com facade de compatibilidade em `mapping/services/priorizacao_territorial.py`.

## 4) Fluxos principais de dados e controle

### 4.1 Ciclo científico de revisão
1. Usuário contribui/atualiza ponto georreferenciado.
2. Endpoint científico calcula candidatos de predição e confiança.
3. Ponto entra na fila de revisão quando há necessidade de validação humana.
4. Revisor/admin valida via endpoints científicos protegidos.
5. Decisões e transições são persistidas em modelos de histórico de validação.
6. Dashboard e priorização territorial agregam indicadores operacionais/científicos.

### 4.2 Ciclo de enriquecimento
1. Planta/ponto é submetido aos endpoints de enriquecimento.
2. Pipeline consulta provedores taxonômicos e de biodiversidade.
3. Lógica de normalização e confiança consolida campos canônicos.
4. Status e payload resumido são persistidos com rastreabilidade por fonte.

### 4.3 Ciclo ambiental e territorial
1. Endpoints de clima e MapBiomas buscam/sincronizam contexto externo.
2. Alertas e dados contextuais são expostos para fluxos administrativos e analíticos.
3. Priorização territorial consome clima + densidade de validação + recência.

### 4.4 Ciclo de paridade mobile
1. Mobile consome base de API canônica a partir de `EXPO_PUBLIC_API_URL`.
2. Endpoints de paridade mobile entregam previews normalizados de mapa e payloads de metadados/download offline.
3. Pipeline compartilhado de identificação preserva paridade contratual entre web e mobile.

## 5) Revisão humana e controles de governança

- Endpoints sensíveis à revisão usam checagens de revisor/admin (`IsReviewerOrAdmin` e validações de papel/grupo).
- A saída de IA é assistiva; a decisão científica final é explicitamente humana.
- Modelos de histórico de validação fornecem rastreabilidade/auditabilidade de transições do ciclo.
- Serviços de saúde de integração oferecem visibilidade operacional de dependências externas.

## 6) Testes e verificação arquitetural

A suíte automatizada atual valida contratos arquiteturais centrais:
- lógica de risco/priorização científica,
- fronteiras de permissão de revisão,
- comportamento do pipeline de enriquecimento e falhas parciais,
- classificação de status/saúde de integrações,
- serviços climáticos e ambientais,
- cenários de mapbiomas e identificação.

## 7) Restrições arquiteturais atuais

- O app `mapping` ainda concentra múltiplos contextos de domínio.
- Famílias de endpoints legadas e modernas coexistem no mesmo namespace do projeto.
- Algumas integrações são opcionais e sensíveis ao ambiente (chaves/rede/timeout).

Essas restrições são mitigadas atualmente por separação em serviços/domínios e endpoints operacionais explícitos de health.


## 8) Notas arquiteturais de fluxos mobile avançados

- O mobile adota arquitetura orientada a contrato de API com registro de endpoints em `mobile/src/config/api.js` e orquestração em `mobile/src/services/*`.
- A operação offline-first usa persistência local + semântica de fila de sync, com reconciliação no ciclo científico backend.
- Identificação por imagem e IA assistiva são arquiteturalmente subordinadas à validação humana.
- AR e identificação avançada são camadas opcionais e não redefinem o modelo de governança científica central.

Anexo canônico detalhado: [`fluxos-mobile-avancados.md`](./fluxos-mobile-avancados.md).
