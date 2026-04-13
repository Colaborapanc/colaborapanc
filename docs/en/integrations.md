# Integrations

## Current Integration Domains

- Plant identification providers (multi-provider IA flow).
- Taxonomic/biodiversity enrichment services.
- Wikimedia/Wikipedia controlled enrichment.
- MapBiomas environmental alerts.
- Climate alert providers and synchronization.

## Technical Entry Points

- `mapping/services/ia_identificacao.py`
- `mapping/services/plant_identification_service.py`
- `mapping/services/gbif_enrichment_service.py`
- `mapping/services/inaturalist_enrichment_service.py`
- `mapping/services/environment/mapbiomas.py`
- `mapping/services/mapbiomas_alert_service.py`
- `mapping/services/environmental_monitor_service.py`
- `mapping/services/integrations/healthcheck.py`

## Monitoring

- Admin panel: `/painel-admin/integracoes/`
- Health endpoint: `/api/admin/integracoes/health/`
- Quick tests endpoint: `/api/admin/integracoes/testar/`
