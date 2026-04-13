# Deploy

## Requisitos mínimos
- PostgreSQL/PostGIS disponível e acessível.
- Variáveis de ambiente de produção configuradas.
- Dependências Python e geoespaciais instaladas.
- Estratégia de arquivos estáticos e mídia (`collectstatic`, storage).

## Passo a passo base (backend)
1. Provisionar ambiente Linux com Python e GDAL.
2. Configurar banco PostGIS.
3. Definir `.env` de produção (`DEBUG=False`).
4. Instalar dependências e rodar migrações.
5. Executar `collectstatic`.
6. Subir aplicação com WSGI (`config/wsgi.py`) via Gunicorn/uWSGI e proxy reverso.

## Mobile
- Build Expo conforme ambiente (preview/prod), com `EXPO_PUBLIC_API_URL` apontando para backend público.

## Cuidados
- Revisar CORS/CSRF com hosts oficiais.
- Certificados TLS obrigatórios.
- Política de backup para banco e mídia.
- Rotação de segredos e chaves de API.
