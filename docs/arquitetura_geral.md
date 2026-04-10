# Arquitetura geral do ColaboraPANC

## Visão de alto nível
O sistema é composto por:
1. **Backend Django/DRF** (`config/` + `mapping/`).
2. **Banco relacional geoespacial** (PostgreSQL/PostGIS).
3. **Cliente mobile Expo/React Native** (`mobile/`).
4. **Integrações externas** para IA botânica e dados ambientais.

## Backend
### Núcleo Django
- Configuração: `config/settings.py`, `config/urls.py`.
- URL principal inclui `mapping.urls`.
- Autenticação web via `django-allauth` e sessão DRF (`SessionAuthentication`).

### App `mapping`
- **Modelos**: mapeamento de PANC, catálogo botânico, validação científica, gamificação, comunicação, rotas, offline, AR.
- **Views**:
  - `views.py`: rotas web e endpoints legados.
  - `views_api.py`: APIs REST e núcleo científico.
  - `views_offline_plantas.py`, `views_ar_identificacao.py`, `views_mapbiomas.py`.
- **Serialização**: `mapping/serializers.py`.
- **Permissões**: `mapping/permissions.py`.
- **Sinais**: `mapping/signals.py` (pontuação e progressão de gamificação).
- **Comandos**: `mapping/management/commands/`.

## Banco de dados
- Engine configurada: `django.contrib.gis.db.backends.postgis`.
- Entidade central geográfica: `PontoPANC` com `PointField` (`localizacao`) e metadados lat/lon.
- Auditoria científica com `PredicaoIA`, `ValidacaoEspecialista`, `HistoricoValidacao`.

## Mobile
- App principal em `mobile/App.js` (stack navigator).
- Serviços de integração em `mobile/src/services/`.
- Configuração de API central em `mobile/src/config/api.js` via `EXPO_PUBLIC_API_URL`.
- Há coexistência com `mobile/index.tsx` (expo-router), o que exige padronização futura.

## Fluxo de dados (resumo)
1. Usuário cadastra ponto (`PontoPANC`) com geolocalização e foto.
2. Endpoint científico executa inferência e gera `PredicaoIA`.
3. Caso necessário, ponto entra na fila de revisão.
4. Revisor valida/rejeita e gera `ValidacaoEspecialista`.
5. Evento é registrado em `HistoricoValidacao`.
6. Dashboard agrega métricas e priorização territorial.

## Integrações externas
- **PlantNet / Plant.id**: identificação botânica por imagem.
- **INMET / Open-Meteo**: dados/alertas climáticos.
- **MapBiomas**: consultas de alertas territoriais e contexto ambiental.

## Observações arquiteturais importantes
- O projeto concentra muitas responsabilidades no app `mapping`.
- Há endpoints legados e novos coexistindo no mesmo namespace `/api/`.
- Recomenda-se evolução por modularização de domínios e versionamento explícito de API.
