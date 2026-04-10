# MapBiomas Alert API integration

## Overview

Integration with the MapBiomas Alerta API allows the ColaboraPANC system to consult deforestation alerts, territories and rural properties throughout Brazil. This functionality is especially useful for:

- Monitor conservation areas close to PANC points
- Alert users about deforestation in regions of interest
- Analyze environmental impacts in areas where PANCs are cultivated
- Generate sustainability reports

## Official Documentation

- **Platform**: https://plataforma.alerta.mapbiomas.org/
- **API documentation**: https://plataforma.alerta.mapbiomas.org/api/docs/
- **GraphQL Endpoint**: https://plataforma.alerta.mapbiomas.org/api/v2/graphql

## Configuration

### 1. Credentials

To use the MapBiomas API, you need to create a free account:

1. Visit: https://plataforma.alerta.mapbiomas.org/signup
2. Fill out the registration form
3. Confirm your email
4. Add your credentials in the `.env` file:
```bash
MAPBIOMAS_EMAIL=your-email@example.com
MAPBIOMAS_PASSWORD=your-secure-password
```
### 2. Cache

The integration uses Django's caching system to reduce API calls:

- **Authentication token**: 23 hours
- **Alerts**: 1 hour
- **Detailed alert**: 24 hours
- **Territories**: 7 days
- **Property Alerts**: 6 hours
- **Point information**: 24 hours
- **PANC point alerts**: 3 hours

## Available Endpoints

### 1. Test Connection

Tests authentication with the MapBiomas API.

**Endpoint:** `GET /api/mapbiomas/testar/`

**Permissions:** Public (AllowAny)

**Successful Response:**
```json
{
  "status": "success",
  "message": "Connection to MapBiomas established successfully",
  "autenticado": true
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Could not authenticate with the MapBiomas API. Check credentials.",
  "autenticado": false
}
```
### 2. Search for Deforestation Alerts

Search for deforestation alerts in a specific region.

**Endpoint:** `GET /api/mapbiomas/alertas/`

**Permissions:** Public (AllowAny)

**Query Parameters:**

| Parameter | Type | Mandatory | Description | Standard |
|-----------|------|-------------|-----------|--------|
| latitude | float | No | Center point latitude | - |
| longitude | float | No | Center point longitude | - |
| radius_km | float | No | Search radius in km | 10 |
| start_date | string | No | Start date (YYYY-MM-DD) | 90 days ago |
| end_date | string | No | End date (YYYY-MM-DD) | Today |
| territory_ids | string | No | Comma separated territory IDs | - |
| limit | int | No | Maximum number of results | 100 |
| page | int | No | Page number | 1 |

**Request Example:**
```bash
curl "http://localhost:8000/api/mapbiomas/alertas/?latitude=-15.7801&longitude=-47.9292&raio_km=20&limite=10"
```

**Successful Response:**
```json
{
  "collection": [
    {
      "alertCode": 123456,
      "detectedAt": "2025-01-15",
      "publishedAt": "2025-01-20",
      "areaHa": 25.5,
      "alertGeometry": "...",
      "crossedBiomes": ["Cerrado"],
      "crossedCities": ["Brasília"],
      "crossedStates": ["DF"],
      "publishedImages": ["..."]
    }
  ],
  "metadata": {
    "totalCount": 150,
    "totalPages": 15,
    "currentPage": 1
  }
}
```
### 3. Fetch Detailed Alert

Searches for detailed information for a specific alert.

**Endpoint:** `GET /api/mapbiomas/alertas/<alert_code>/`

**Permissions:** Public (AllowAny)

**Request Example:**
```bash
curl "http://localhost:8000/api/mapbiomas/alertas/123456/"
```

**Successful Response:**
```json
{
  "alertCode": 123456,
  "detectedAt": "2025-01-15",
  "publishedAt": "2025-01-20",
  "areaHa": 25.5,
  "statusName": "published",
  "alertGeometry": "...",
  "crossedBiomes": ["Cerrado"],
  "crossedCities": ["Brasília"],
  "crossedStates": ["DF"],
  "crossedIndigenousLands": [],
  "crossedQuilombos": [],
  "crossedConservationUnits": [],
  "crossedRuralProperties": ["CAR123456"],
  "publishedImages": ["..."],
  "imagesLabels": ["..."],
  "classesLabels": ["..."]
}
```
### 4. Search for Territories

Search for available territories (biomes, municipalities, conservation units, etc.).

**Endpoint:** `GET /api/mapbiomas/territorios/`

**Permissions:** Public (AllowAny)

**Query Parameters:**

| Parameter | Type | Mandatory | Description | Standard |
|-----------|------|-------------|-----------|--------|
| category | string | No | Territory category (BIOME, MUNICIPALITY, etc.) | - |
| name | string | No | Name of the territory to search | - |
| limit | int | No | Maximum number of results | 100 |

**Request Example:**
```bash
curl "http://localhost:8000/api/mapbiomas/territorios/?categoria=BIOME"
```

**Successful Response:**
```json
[
  {
    "name": "Amazônia",
    "category": "BIOME",
    "categoryName": "Bioma"
  },
  {
    "name": "Cerrado",
    "category": "BIOME",
    "categoryName": "Bioma"
  }
]
```
### 5. Search for Alerts by Rural Property

Searches for alerts associated with a specific rural property (CAR).

**Endpoint:** `GET /api/mapbiomas/property/`

**Permissions:** Public (AllowAny)

**Query Parameters:**

| Parameter | Type | Mandatory | Description |
|-----------|------|-------------|-----------|
| car_code | string | Yes | Property CAR code |
| start_date | string | No | Start date (YYYY-MM-DD) |
| end_date | string | No | End date (YYYY-MM-DD) |

**Request Example:**
```bash
curl "http://localhost:8000/api/mapbiomas/propriedade/?car_code=DF-1234567890123456789012345678901234"
```

**Successful Response:**
```json
{
  "carCode": "DF-1234567890123456789012345678901234",
  "propertyName": "Fazenda Exemplo",
  "totalAreaHa": 500.0,
  "alerts": [
    {
      "alertCode": 123456,
      "detectedAt": "2025-01-15",
      "publishedAt": "2025-01-20",
      "areaHa": 25.5
    }
  ]
}
```
### 6. Information about a Point

Gets information about alerts and territories at a specific point.

**Endpoint:** `GET /api/mapbiomas/ponto/`

**Permissions:** Public (AllowAny)

**Query Parameters:**

| Parameter | Type | Mandatory | Description |
|-----------|------|-------------|-----------|
| latitude | float | Yes | Point latitude |
| longitude | float | Yes | Point longitude |

**Request Example:**
```bash
curl "http://localhost:8000/api/mapbiomas/ponto/?latitude=-15.7801&longitude=-47.9292"
```
### 7. Check Alerts Near PANC Point

Check deforestation alerts near a specific PANC point registered in the system.

**Endpoint:** `GET /api/mapbiomas/pontos-panc/<ponto_id>/`

**Permissions:** Authenticated (IsAuthenticated)

**Query Parameters:**

| Parameter | Type | Mandatory | Description | Standard |
|-----------|------|-------------|-----------|--------|
| radius_km | float | No | Search radius in km | 5 |

**Request Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/mapbiomas/pontos-panc/123/?raio_km=10"
```

**Successful Response:**
```json
{
  "ponto_id": 123,
  "ponto_nome": "Ora-pro-nóbis na Praça",
  "latitude": -15.7801,
  "longitude": -47.9292,
  "raio_busca_km": 10,
  "alertas": [
    {
      "alertCode": 123456,
      "detectedAt": "2025-01-15",
      "publishedAt": "2025-01-20",
      "areaHa": 25.5,
      "alertGeometry": "...",
      "crossedBiomes": ["Cerrado"],
      "crossedCities": ["Brasília"],
      "crossedStates": ["DF"]
    }
  ],
  "total_alertas": 3,
  "area_total_desmatada_ha": 75.5,
  "metadata": {
    "totalCount": 3,
    "totalPages": 1,
    "currentPage": 1
  }
}
```
## Programmatic Use

### Python (Service)
```python
from mapping.services.mapbiomas_service import mapbiomas_service

# Buscar alertas em uma região
alertas = mapbiomas_service.buscar_alertas(
    latitude=-15.7801,
    longitude=-47.9292,
    raio_km=20,
    data_inicio='2025-01-01',
    data_fim='2025-01-31'
)

# Buscar detalhes de um alerta
alerta_detalhado = mapbiomas_service.buscar_alerta_detalhado(alert_code='123456')

# Buscar territórios
territorios = mapbiomas_service.buscar_territorios(categoria='BIOME')

# Verificar alertas próximos a um ponto PANC
resultado = mapbiomas_service.verificar_alertas_proximos_ponto_panc(
    ponto_panc_id=123,
    raio_km=10
)
```
### JavaScript/TypeScript (Mobile App)
```typescript
import axios from 'axios';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL;

// Buscar alertas
const buscarAlertas = async (latitude: number, longitude: number, raioKm: number = 10) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/mapbiomas/alertas/`, {
      params: {
        latitude,
        longitude,
        raio_km: raioKm,
        limite: 20
      }
    });
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar alertas MapBiomas:', error);
    return null;
  }
};

// Verificar alertas próximos a um ponto PANC
const verificarAlertasPonto = async (pontoId: number, token: string) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/mapbiomas/pontos-panc/${pontoId}/`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params: {
          raio_km: 5
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error while checking alerts near the point:', error);
    return null;
  }
};
```
## Use Cases

### 1. PANC Point Monitoring

Check if there are deforestation alerts near registered PANC points:
```python
# No momento do cadastro de um novo ponto
ponto = PontoPANC.objects.get(id=123)
resultado = mapbiomas_service.verificar_alertas_proximos_ponto_panc(
    ponto_panc_id=ponto.id,
    raio_km=5
)

if resultado['total_alertas'] > 0:
    # Notificar o usuário sobre desmatamento próximo
    enviar_notificacao(
        usuario=ponto.criado_por,
        titulo="Alerta de Desmatamento",
        mensagem=f"Detectados {resultado['total_alertas']} alertas de desmatamento "
                f"a menos de 5km do seu ponto PANC '{ponto.nome_popular}'"
    )
```
### 2. Sustainability Dashboard

Create a dashboard showing environmental statistics:
```python
from django.db.models import Count
from mapping.models import PontoPANC

# Para cada bioma, contar pontos PANC e alertas
biomas = ['Amazônia', 'Cerrado', 'Mata Atlântica', 'Caatinga', 'Pampa', 'Pantanal']
dashboard_data = []

for bioma in biomas:
    # Buscar territórios do bioma
    territorios = mapbiomas_service.buscar_territorios(
        categoria='BIOME',
        nome=bioma
    )

    if territorios:
        # Buscar alertas no bioma (últimos 30 dias)
        alertas = mapbiomas_service.buscar_alertas(
            territorio_ids=[t['id'] for t in territorios],
            data_inicio=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )

        dashboard_data.append({
            'bioma': bioma,
            'total_alertas': alertas['metadata']['totalCount'],
            'area_desmatada_ha': sum(a['areaHa'] for a in alertas['collection'])
        })
```
### 3. Advanced Search Filter

Allow users to filter PANC points by regions without recent deforestation:
```python
def buscar_pontos_em_areas_preservadas(raio_km=10, dias_verificacao=180):
    """
    Busca pontos PANC que NÃO têm alertas de desmatamento próximos
    """
    pontos_seguros = []

    for ponto in PontoPANC.objects.filter(status_validacao='aprovado'):
        resultado = mapbiomas_service.verificar_alertas_proximos_ponto_panc(
            ponto_panc_id=ponto.id,
            raio_km=raio_km
        )

        if resultado['total_alertas'] == 0:
            pontos_seguros.append(ponto)

    return pontos_seguros
```
## Limitations and Considerations

### Rate Limits

The MapBiomas API does not specify explicit rate limits in the documentation, but it is recommended:

- Use the implemented cache system
- Avoid unnecessary requests
- Implement retry with exponential backoff in case of failures

### Data Coverage

- **Period**: Alerts available since 2019
- **Area**: The entire Brazilian territory
- **Update**: Alerts are published periodically
- **Accuracy**: Minimum detection area varies by sensor

### Performance

- Queries with very large bounding boxes can take time
- Use paging for large volumes of data
- Configure appropriate cache to reduce latency

## Troubleshooting

### Error 401: Unauthorized

Check that the credentials in `.env` are correct:
```bash
MAPBIOMAS_EMAIL=your-email@example.com
MAPBIOMAS_PASSWORD=your-password
```
### Error 503: Service Unavailable

The API may be temporarily unavailable:

- Check the status at: https://plataforma.alerta.mapbiomas.org/
- Try again after a few minutes
- Implement retry logic

### Cache doesn't work

Check if Django cache is configured:
```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```
## Additional Resources

- **Web Platform**: https://plataforma.alerta.mapbiomas.org/
- **Full Documentation**: https://plataforma.alerta.mapbiomas.org/api/docs/
- **Support**: Get in touch through the platform
- **Source Code**: `/home/user/colaborapanc/mapping/services/mapbiomas_service.py`

## Changelog

### v1.0.0 (2026-01-23)

- Initial implementation of MapBiomas integration
- Authentication via GraphQL
- Endpoints to search for alerts, territories and properties
- Integrated cache system
- Checking alerts near PANC points
- Automated tests