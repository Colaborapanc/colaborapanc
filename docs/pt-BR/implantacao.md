# Implantação

## Requisitos mínimos

- Banco PostgreSQL/PostGIS em ambiente de produção.
- Gestão adequada de segredos e variáveis de ambiente.
- Estratégia para estáticos/mídia (`collectstatic`, armazenamento).
- Proxy reverso + runtime WSGI/ASGI.

## Checklist mínimo de deploy

1. Definir `DJANGO_SECRET_KEY`, debug, hosts e variáveis de banco.
2. Aplicar migrações: `python manage.py migrate`.
3. Coletar estáticos: `python manage.py collectstatic --noinput`.
4. Validar healthcheck: `GET /healthz/`.
5. Executar smoke tests de APIs críticas (fluxo científico, mapbiomas, clima, mobile parity).

## Endpoints operacionais

- Health check: `/healthz/`
- Painel de integrações: `/painel-admin/integracoes/`
- API de saúde de integrações: `/api/admin/integracoes/health/`
