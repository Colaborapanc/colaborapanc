# Admin Guide

## Admin Surfaces

- Django admin: `/admin/`
- Integration panel: `/painel-admin/integracoes/`
- Validation panel: `/painel-validacao/`
- Gamification admin: `/gamificacao/admin/`

## Common Admin Tasks

- Monitor integration status and run test calls.
- Review scientific queue and validate/reject pending points.
- Export users and points CSV files.
- Trigger operational management commands when required.

## Management Commands (examples)

- `python manage.py auditar_integracoes_funcionais`
- `python manage.py sincronizar_alertas_climaticos`
- `python manage.py sincronizar_alertas_ambientais`
- `python manage.py processar_plantas`
