# Integrações

## Domínios de integração atuais

- Provedores de identificação botânica (fluxo IA multiprovedor).
- Serviços de enriquecimento taxonômico/biodiversidade.
- Enriquecimento controlado via Wikimedia/Wikipedia.
- Alertas ambientais do MapBiomas.
- Provedores de alerta climático e sincronização.

## Pontos de entrada técnicos

- `mapping/services/ia_identificacao.py`
- `mapping/services/plant_identification_service.py`
- `mapping/services/gbif_enrichment_service.py`
- `mapping/services/inaturalist_enrichment_service.py`
- `mapping/services/environment/mapbiomas.py`
- `mapping/services/mapbiomas_alert_service.py`
- `mapping/services/environmental_monitor_service.py`
- `mapping/services/integrations/healthcheck.py`

## Monitoramento

- Painel administrativo: `/painel-admin/integracoes/`
- Endpoint de saúde: `/api/admin/integracoes/health/`
- Endpoint de testes rápidos: `/api/admin/integracoes/testar/`
