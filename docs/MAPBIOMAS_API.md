# Integração MapBiomas Alerta API

## Visão Geral

A integração com a API MapBiomas Alerta permite ao sistema ColaboraPANC consultar alertas de desmatamento, territórios e propriedades rurais em todo o Brasil. Esta funcionalidade é especialmente útil para:

- Monitorar áreas de conservação próximas a pontos PANC
- Alertar usuários sobre desmatamento em regiões de interesse
- Analisar impactos ambientais em áreas onde as PANCs são cultivadas
- Gerar relatórios de sustentabilidade

## Documentação Oficial

- **Plataforma**: https://plataforma.alerta.mapbiomas.org/
- **Documentação da API**: https://plataforma.alerta.mapbiomas.org/api/docs/
- **GraphQL Endpoint**: https://plataforma.alerta.mapbiomas.org/api/v2/graphql

## Configuração

### 1. Credenciais

Para usar a API MapBiomas, você precisa criar uma conta gratuita:

1. Acesse: https://plataforma.alerta.mapbiomas.org/signup
2. Preencha o formulário de cadastro
3. Confirme seu e-mail
4. Adicione suas credenciais no arquivo `.env`:

```bash
MAPBIOMAS_EMAIL=seu-email@example.com
MAPBIOMAS_PASSWORD=sua-senha-segura
```

### 2. Cache

A integração utiliza o sistema de cache do Django para reduzir chamadas à API:

- **Token de autenticação**: 23 horas
- **Alertas**: 1 hora
- **Alerta detalhado**: 24 horas
- **Territórios**: 7 dias
- **Alertas de propriedade**: 6 horas
- **Informações de ponto**: 24 horas
- **Alertas de ponto PANC**: 3 horas

## Endpoints Disponíveis

### 1. Testar Conexão

Testa a autenticação com a API MapBiomas.

**Endpoint:** `GET /api/mapbiomas/testar/`

**Permissões:** Público (AllowAny)

**Resposta de Sucesso:**
```json
{
  "status": "sucesso",
  "mensagem": "Conexão com MapBiomas estabelecida com sucesso",
  "autenticado": true
}
```

**Resposta de Erro:**
```json
{
  "status": "erro",
  "mensagem": "Não foi possível autenticar na API MapBiomas. Verifique as credenciais.",
  "autenticado": false
}
```

### 2. Buscar Alertas de Desmatamento

Busca alertas de desmatamento em uma região específica.

**Endpoint:** `GET /api/mapbiomas/alertas/`

**Permissões:** Público (AllowAny)

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição | Padrão |
|-----------|------|-------------|-----------|--------|
| latitude | float | Não | Latitude do ponto central | - |
| longitude | float | Não | Longitude do ponto central | - |
| raio_km | float | Não | Raio de busca em km | 10 |
| data_inicio | string | Não | Data inicial (YYYY-MM-DD) | 90 dias atrás |
| data_fim | string | Não | Data final (YYYY-MM-DD) | Hoje |
| territorio_ids | string | Não | IDs de territórios separados por vírgula | - |
| limite | int | Não | Número máximo de resultados | 100 |
| pagina | int | Não | Número da página | 1 |

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/api/mapbiomas/alertas/?latitude=-15.7801&longitude=-47.9292&raio_km=20&limite=10"
```

**Resposta de Sucesso:**
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

### 3. Buscar Alerta Detalhado

Busca informações detalhadas de um alerta específico.

**Endpoint:** `GET /api/mapbiomas/alertas/<alert_code>/`

**Permissões:** Público (AllowAny)

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/api/mapbiomas/alertas/123456/"
```

**Resposta de Sucesso:**
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

### 4. Buscar Territórios

Busca territórios disponíveis (biomas, municípios, unidades de conservação, etc.).

**Endpoint:** `GET /api/mapbiomas/territorios/`

**Permissões:** Público (AllowAny)

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição | Padrão |
|-----------|------|-------------|-----------|--------|
| categoria | string | Não | Categoria do território (BIOME, MUNICIPALITY, etc.) | - |
| nome | string | Não | Nome do território para busca | - |
| limite | int | Não | Número máximo de resultados | 100 |

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/api/mapbiomas/territorios/?categoria=BIOME"
```

**Resposta de Sucesso:**
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

### 5. Buscar Alertas por Propriedade Rural

Busca alertas associados a uma propriedade rural específica (CAR).

**Endpoint:** `GET /api/mapbiomas/propriedade/`

**Permissões:** Público (AllowAny)

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| car_code | string | Sim | Código CAR da propriedade |
| data_inicio | string | Não | Data inicial (YYYY-MM-DD) |
| data_fim | string | Não | Data final (YYYY-MM-DD) |

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/api/mapbiomas/propriedade/?car_code=DF-1234567890123456789012345678901234"
```

**Resposta de Sucesso:**
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

### 6. Informações sobre um Ponto

Obtém informações sobre alertas e territórios em um ponto específico.

**Endpoint:** `GET /api/mapbiomas/ponto/`

**Permissões:** Público (AllowAny)

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| latitude | float | Sim | Latitude do ponto |
| longitude | float | Sim | Longitude do ponto |

**Exemplo de Requisição:**
```bash
curl "http://localhost:8000/api/mapbiomas/ponto/?latitude=-15.7801&longitude=-47.9292"
```

### 7. Verificar Alertas Próximos a Ponto PANC

Verifica alertas de desmatamento próximos a um ponto PANC específico cadastrado no sistema.

**Endpoint:** `GET /api/mapbiomas/pontos-panc/<ponto_id>/`

**Permissões:** Autenticado (IsAuthenticated)

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição | Padrão |
|-----------|------|-------------|-----------|--------|
| raio_km | float | Não | Raio de busca em km | 5 |

**Exemplo de Requisição:**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/mapbiomas/pontos-panc/123/?raio_km=10"
```

**Resposta de Sucesso:**
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

## Uso Programático

### Python (Serviço)

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

### JavaScript/TypeScript (App Mobile)

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
    console.error('Erro ao verificar alertas do ponto:', error);
    return null;
  }
};
```

## Casos de Uso

### 1. Monitoramento de Pontos PANC

Verificar se há alertas de desmatamento próximos a pontos PANC cadastrados:

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

### 2. Dashboard de Sustentabilidade

Criar um painel mostrando estatísticas ambientais:

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

### 3. Filtro de Busca Avançado

Permitir usuários filtrar pontos PANC por regiões sem desmatamento recente:

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

## Limitações e Considerações

### Rate Limits

A API MapBiomas não especifica rate limits explícitos na documentação, mas é recomendado:

- Usar o sistema de cache implementado
- Evitar requisições desnecessárias
- Implementar retry com backoff exponencial em caso de falhas

### Cobertura de Dados

- **Período**: Alertas disponíveis desde 2019
- **Área**: Todo o território brasileiro
- **Atualização**: Alertas são publicados periodicamente
- **Precisão**: Área mínima de detecção varia por sensor

### Performance

- Queries com bounding box muito grandes podem demorar
- Use paginação para grandes volumes de dados
- Configure cache adequado para reduzir latência

## Solução de Problemas

### Erro 401: Unauthorized

Verifique se as credenciais no `.env` estão corretas:

```bash
MAPBIOMAS_EMAIL=seu-email@example.com
MAPBIOMAS_PASSWORD=sua-senha
```

### Erro 503: Service Unavailable

A API pode estar temporariamente indisponível:

- Verifique o status em: https://plataforma.alerta.mapbiomas.org/
- Tente novamente após alguns minutos
- Implemente retry logic

### Cache não funciona

Verifique se o cache do Django está configurado:

```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

## Recursos Adicionais

- **Plataforma Web**: https://plataforma.alerta.mapbiomas.org/
- **Documentação Completa**: https://plataforma.alerta.mapbiomas.org/api/docs/
- **Suporte**: Entre em contato através da plataforma
- **Código Fonte**: `/home/user/colaborapanc/mapping/services/mapbiomas_service.py`

## Changelog

### v1.0.0 (2026-01-23)

- Implementação inicial da integração MapBiomas
- Autenticação via GraphQL
- Endpoints para buscar alertas, territórios e propriedades
- Sistema de cache integrado
- Verificação de alertas próximos a pontos PANC
- Testes automatizados
