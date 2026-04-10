# Instalação

## Escopo

Este guia cobre setup local de:

- Backend (Django + DRF)
- Banco geoespacial (PostgreSQL + PostGIS)
- Dependências GIS (GDAL)
- Aplicativo mobile (Expo/React Native)

Para implantação em produção, consulte [`implantacao.md`](./implantacao.md).

## 1) Pré-requisitos reais

### Ferramentas do host
- Python **3.11+**
- `pip` + suporte a ambiente virtual (`venv`)
- Node.js **18+** e npm (mobile)
- PostgreSQL **15+** com extensão PostGIS
- Bibliotecas GDAL em nível de sistema para o binding Python de GDAL

### Arquivos do repositório usados neste setup
- Dependências Python: `requirements_core.txt` (recomendado) e `requirements.txt` (conjunto legado mais amplo)
- Base de contêiner: `Dockerfile`, `docker-compose.yml`
- Configurações Django e leitura de ambiente: `config/settings.py`

## 2) Variáveis de ambiente (backend + mobile)

O Django lê `.env` automaticamente quando `python-dotenv` está disponível.

### Variáveis mínimas do backend para execução local

```dotenv
DJANGO_SECRET_KEY=troque-isto
DJANGO_DEBUG=True
POSTGRES_DB=pancdb
POSTGRES_USER=pancuser
POSTGRES_PASSWORD=pancpass123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Variáveis opcionais frequentes
- `CORS_ALLOWED_ORIGINS`
- `PLANTNET_API_KEY`
- `PLANTID_API_KEY`
- `MAPBIOMAS_EMAIL`, `MAPBIOMAS_PASSWORD`, `MAPBIOMAS_API_URL`
- `NASA_FIRMS_MAP_KEY`

### Variável do mobile

```dotenv
EXPO_PUBLIC_API_URL=http://localhost:8000
```

> Em dispositivo físico, `localhost` aponta para o próprio aparelho. Use IP da máquina host ou URL de túnel.

## 3) Setup de banco e PostGIS

### Opção A — PostgreSQL local
1. Criar banco/usuário.
2. Habilitar PostGIS no banco alvo:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Ajustar variáveis `POSTGRES_*`.

### Opção B — serviço de banco no Docker Compose

```bash
docker compose up -d db
```

O compose provisiona `postgis/postgis:15-3.3` e expõe a porta `5432`.

## 4) Dependências GIS (GDAL)

O projeto depende de GDAL no sistema operacional e no pacote Python.

Pacotes Linux típicos:
- `gdal-bin`
- `libgdal-dev`
- `python3-gdal`

Em contêiner, essas dependências já são instaladas pelo `Dockerfile`.

## 5) Setup do backend (local, sem Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_core.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

URL padrão: `http://localhost:8000`.

## 6) Setup do backend com Docker Compose

1. Criar arquivo `.env` local (mesmo diretório de `docker-compose.yml`).
2. Definir no mínimo:
   ```dotenv
   DJANGO_SECRET_KEY=troque-isto
   DJANGO_DEBUG=True
   POSTGRES_DB=pancdb
   POSTGRES_USER=pancuser
   POSTGRES_PASSWORD=pancpass123
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```
3. Subir serviços:
   ```bash
   docker compose up --build
   ```

O comando do backend no compose aplica migrações e sobe o servidor de desenvolvimento.

## 7) Setup do mobile (Expo)

```bash
cd mobile
npm install
npm start
```

Scripts úteis:
- `npm run android`
- `npm run ios`
- `npm run web`
- `npm run doctor`
- `npm run test:ci`

## 8) Fluxo mínimo funcional (sanity check)

Com backend no ar:
1. Abrir `http://localhost:8000/`.
2. Validar health endpoint: `http://localhost:8000/healthz/`.
3. (Opcional) Confirmar endpoint de autenticação: `POST /api/token/login/`.
4. Executar testes:
   ```bash
   pytest
   ```

## 9) Erros comuns e observações operacionais

### `DJANGO_SECRET_KEY` não definido
- Causa: variável ausente no ambiente.
- Correção: definir `DJANGO_SECRET_KEY` no `.env`.

### Erro de migração PostGIS/GIS
- Causa: banco sem extensão PostGIS ou falta de GDAL no sistema.
- Correção: habilitar extensão `postgis` e instalar pacotes GDAL.

### Backend não conecta no banco via Docker
- Causa comum: `POSTGRES_HOST=localhost` dentro do contêiner.
- Correção: usar `POSTGRES_HOST=db` no compose.

### Erros de CORS no navegador/mobile
- Correção: configurar `CORS_ALLOWED_ORIGINS` com origens exatas.

### Mobile não alcança API
- Correção: em dispositivo físico, usar IP da máquina host/URL pública em `EXPO_PUBLIC_API_URL`, não `localhost`.
