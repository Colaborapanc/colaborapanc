# Implantação

## Escopo

Este guia cobre implantação orientada a produção para:

- Runtime da aplicação backend
- Banco PostgreSQL/PostGIS
- Dependências GIS e tratamento de estáticos/mídia
- Abordagens com e sem contêiner
- Alinhamento do app mobile ao backend publicado

Para setup local de desenvolvimento, consulte [`instalacao.md`](./instalacao.md).

## 1) Pré-requisitos de produção

### Base de infraestrutura
- Host Linux/VM/plataforma de contêiner
- Runtime Python 3.11 (quando não containerizado)
- PostgreSQL com PostGIS habilitado
- Proxy reverso (ex.: Nginx) na frente do servidor Django
- Certificados TLS para endpoints públicos

### Base da aplicação
- Variáveis de ambiente definidas com segurança (sem segredo em texto puro no repositório)
- `DJANGO_SECRET_KEY` definido
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS` configurado para domínios/IPs reais
- Variáveis de banco (`POSTGRES_*`) alinhadas ao banco de produção

## 2) Checklist de variáveis de ambiente

### Obrigatórias em produção
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT` (se fora do padrão)

### Fortemente recomendadas
- `CORS_ALLOWED_ORIGINS`
- Variáveis de backend de e-mail (`EMAIL_HOST`, `EMAIL_PORT`, etc.)
- Chaves de integração apenas quando os serviços correspondentes estiverem habilitados

## 3) Fluxo de banco e migrações

1. Provisionar PostgreSQL/PostGIS.
2. Habilitar extensão PostGIS no banco alvo.
3. Garantir conectividade com credenciais da aplicação.
4. Aplicar migrações:
   ```bash
   python manage.py migrate --noinput
   ```
5. Validar subida da aplicação e consultas críticas.

## 4) Estáticos/mídia e processo da aplicação

Executar coleta de estáticos a cada deploy:

```bash
python manage.py collectstatic --noinput
```

Executar Django com Gunicorn (como no CMD padrão do Dockerfile):

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

Usar proxy reverso para:
- Terminação TLS
- Estratégia de entrega de estáticos/mídia
- Política de headers, buffers e timeouts

## 5) Referência de implantação com contêiner

### Build e execução

```bash
docker compose up --build -d
```

### Observação importante de runtime no compose
- `config/settings.py` consome `POSTGRES_HOST`, não `DB_HOST`.
- Em ambiente containerizado, definir `POSTGRES_HOST=db` no `.env`.

### Persistência de dados
Manter volumes de banco e mídia/estáticos (já declarados em `docker-compose.yml`):
- `postgres_data`
- `static_files`
- `media_files`

## 6) Smoke checks operacionais pós-deploy

- Health check: `GET /healthz/`
- Raiz da aplicação responde: `GET /`
- Rota admin responde: `GET /admin/`
- Painel/API de integrações:
  - `GET /painel-admin/integracoes/`
  - `GET /api/admin/integracoes/health/`
- Smoke opcional de API:
  - `POST /api/token/login/`
  - `GET /api/alertas-ativos/`

## 7) Alinhamento de release mobile

Configurar ambiente mobile para URL pública do backend:

```dotenv
EXPO_PUBLIC_API_URL=https://seu-dominio-api
```

Não publicar build mobile apontando para localhost/hosts privados.

## 8) Problemas comuns em implantação

### `ImproperlyConfigured: DJANGO_SECRET_KEY ...`
- Causa: segredo ausente no runtime.
- Correção: injetar `DJANGO_SECRET_KEY` por secret manager ou `.env`.

### Conexão com banco recusada
- Causa: `POSTGRES_HOST` inválido/rede/firewall.
- Correção: validar host, credenciais, porta e alcance de rede.

### Falhas GIS/PostGIS
- Causa: extensão PostGIS ausente ou incompatibilidade de runtime GDAL.
- Correção: habilitar extensão e garantir pacotes/bibliotecas GDAL.

### Erros CORS/CSRF em produção
- Causa: domínios não listados em hosts/origens permitidos.
- Correção: configurar `DJANGO_ALLOWED_HOSTS` e `CORS_ALLOWED_ORIGINS` explicitamente.

### Estáticos não servidos
- Causa: ausência de `collectstatic` ou proxy sem mapeamento de estáticos.
- Correção: executar `collectstatic` e validar configuração de servidor/proxy.
