# mapping/services/mapbiomas_service.py
# Serviço para integração com a API MapBiomas Alerta
# Documentação: https://plataforma.alerta.mapbiomas.org/api/docs/

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MapBiomasService:
    """
    Serviço para integração com a API MapBiomas Alerta
    Permite consultar alertas de desmatamento, territórios e propriedades rurais
    """

    def __init__(self):
        self.email = os.environ.get('MAPBIOMAS_EMAIL', '')
        self.password = os.environ.get('MAPBIOMAS_PASSWORD', '')
        self.base_url = 'https://plataforma.alerta.mapbiomas.org/api/v2/graphql'
        self.token = None
        self.token_expiry = None

    def _get_token(self) -> Optional[str]:
        """
        Obtém ou renova o token de autenticação

        Returns:
            str: Token de autenticação ou None se falhar
        """
        # Verifica se há token válido em cache
        cached_token = cache.get('mapbiomas_token')
        if cached_token:
            return cached_token

        if not self.email or not self.password:
            logger.warning("Credenciais MapBiomas não configuradas")
            return None

        try:
            # Mutation GraphQL para login
            mutation = """
            mutation SignIn($email: String!, $password: String!) {
                signIn(email: $email, password: $password) {
                    token
                }
            }
            """

            variables = {
                'email': self.email,
                'password': self.password
            }

            response = requests.post(
                self.base_url,
                json={'query': mutation, 'variables': variables},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'signIn' in data['data']:
                    token = data['data']['signIn']['token']
                    # Armazena token em cache por 23 horas (tokens geralmente expiram em 24h)
                    cache.set('mapbiomas_token', token, 23 * 60 * 60)
                    logger.info("Token MapBiomas obtido com sucesso")
                    return token
                else:
                    logger.error(f"Erro na resposta de autenticação MapBiomas: {data}")
                    return None
            else:
                logger.error(f"Erro ao autenticar na API MapBiomas: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Exceção ao obter token MapBiomas: {e}")
            return None

    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """
        Executa uma query GraphQL na API MapBiomas

        Args:
            query: Query GraphQL
            variables: Variáveis da query

        Returns:
            dict: Resposta da API ou None se falhar
        """
        token = self._get_token()
        if not token:
            return None

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            payload = {'query': query}
            if variables:
                payload['variables'] = variables

            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    logger.error(f"Erros GraphQL: {data['errors']}")
                    return None
                return data.get('data')
            else:
                logger.error(f"Erro na requisição MapBiomas: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Exceção ao executar query MapBiomas: {e}")
            return None

    def buscar_alertas(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        raio_km: float = 10,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        territorio_ids: Optional[List[int]] = None,
        limite: int = 100,
        pagina: int = 1
    ) -> Optional[Dict]:
        """
        Busca alertas de desmatamento na região especificada

        Args:
            latitude: Latitude do ponto central
            longitude: Longitude do ponto central
            raio_km: Raio de busca em km (será convertido para bbox)
            data_inicio: Data inicial (formato: YYYY-MM-DD)
            data_fim: Data final (formato: YYYY-MM-DD)
            territorio_ids: IDs de territórios específicos
            limite: Número máximo de resultados
            pagina: Número da página

        Returns:
            dict: Dados dos alertas ou None se falhar
        """
        # Calcula bounding box se lat/lng fornecidos
        bbox = None
        if latitude is not None and longitude is not None:
            bbox = self._calcular_bbox(latitude, longitude, raio_km)

        # Define datas padrão (últimos 90 dias se não especificado)
        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = datetime.now().strftime('%Y-%m-%d')

        query = """
        query GetAlerts(
            $startDate: BaseDate!
            $endDate: BaseDate!
            $boundingBox: [Float!]
            $territoryIds: [Int!]
            $limit: Int
            $page: Int
        ) {
            alerts(
                startDate: $startDate
                endDate: $endDate
                dateType: DetectedAt
                boundingBox: $boundingBox
                territoryIds: $territoryIds
                limit: $limit
                page: $page
            ) {
                collection {
                    alertCode
                    detectedAt
                    publishedAt
                    areaHa
                    alertGeometry
                    crossedBiomes
                    crossedCities
                    crossedStates
                    publishedImages
                }
                metadata {
                    totalCount
                    totalPages
                    currentPage
                }
            }
        }
        """

        variables = {
            'startDate': data_inicio,
            'endDate': data_fim,
            'limit': limite,
            'page': pagina
        }

        if bbox:
            variables['boundingBox'] = bbox
        if territorio_ids:
            variables['territoryIds'] = territorio_ids

        result = self._execute_query(query, variables)

        if result and 'alerts' in result:
            return result['alerts']
        return None

    def buscar_alerta_detalhado(self, alert_code: str) -> Optional[Dict]:
        """
        Busca informações detalhadas de um alerta específico

        Args:
            alert_code: Código do alerta

        Returns:
            dict: Dados detalhados do alerta
        """
        query = """
        query GetAlertDetail($alertCode: Int!) {
            alert(alertCode: $alertCode) {
                alertCode
                detectedAt
                publishedAt
                areaHa
                statusName
                alertGeometry
                crossedBiomes
                crossedCities
                crossedStates
                crossedIndigenousLands
                crossedQuilombos
                crossedConservationUnits
                crossedRuralProperties
                publishedImages
                imagesLabels
                classesLabels
            }
        }
        """

        try:
            alert_code_int = int(alert_code)
        except ValueError:
            logger.error(f"alertCode deve ser um número inteiro: {alert_code}")
            return None

        variables = {'alertCode': alert_code_int}
        result = self._execute_query(query, variables)

        if result and 'alert' in result:
            return result['alert']
        return None

    def buscar_territorios(
        self,
        categoria: Optional[str] = None,
        nome: Optional[str] = None,
        limite: int = 100
    ) -> Optional[List[Dict]]:
        """
        Busca territórios disponíveis (biomas, municípios, UCs, etc.)

        Args:
            categoria: Categoria do território (BIOME, MUNICIPALITY, etc.)
            nome: Nome do território para busca
            limite: Número máximo de resultados

        Returns:
            list: Lista de territórios
        """
        query = """
        query GetTerritories {
            territoryOptions {
                category
                categoryName
                territories {
                    name
                }
            }
        }
        """

        result = self._execute_query(query, {})

        if result and 'territoryOptions' in result:
            # Filtra por categoria e nome se fornecidos
            all_territories = []
            for territory_category in result['territoryOptions']:
                if categoria and territory_category['category'] != categoria:
                    continue

                for territory in territory_category['territories']:
                    if nome and nome.lower() not in territory['name'].lower():
                        continue

                    all_territories.append({
                        'name': territory['name'],
                        'category': territory_category['category'],
                        'categoryName': territory_category['categoryName']
                    })

            # Limita resultados
            return all_territories[:limite]
        return None

    def buscar_alertas_por_propriedade(
        self,
        car_code: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Busca alertas associados a uma propriedade rural específica (CAR)

        Args:
            car_code: Código CAR da propriedade
            data_inicio: Data inicial
            data_fim: Data final

        Returns:
            dict: Alertas da propriedade
        """
        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = datetime.now().strftime('%Y-%m-%d')

        query = """
        query GetPropertyAlerts(
            $carCode: String!
            $startDate: BaseDate!
            $endDate: BaseDate!
        ) {
            ruralPropertyAlerts(
                carCode: $carCode
                startDate: $startDate
                endDate: $endDate
            ) {
                carCode
                propertyName
                totalAreaHa
                alerts {
                    alertCode
                    detectedAt
                    publishedAt
                    areaHa
                }
            }
        }
        """

        variables = {
            'carCode': car_code,
            'startDate': data_inicio,
            'endDate': data_fim
        }

        result = self._execute_query(query, variables)

        if result and 'ruralPropertyAlerts' in result:
            return result['ruralPropertyAlerts']
        return None

    def obter_informacoes_ponto(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict]:
        """
        Obtém informações sobre alertas e territórios em um ponto específico

        Args:
            latitude: Latitude do ponto
            longitude: Longitude do ponto

        Returns:
            dict: Informações do ponto
        """
        query = """
        query GetPointInfo($latitude: Float!, $longitude: Float!) {
            pointInformation(latitude: $latitude, longitude: $longitude) {
                territories {
                    category
                    name
                }
                alerts {
                    alertCode
                    detectedDate
                    areaHa
                }
            }
        }
        """

        variables = {
            'latitude': latitude,
            'longitude': longitude
        }

        result = self._execute_query(query, variables)

        if result and 'pointInformation' in result:
            return result['pointInformation']
        return None

    def _calcular_bbox(
        self,
        latitude: float,
        longitude: float,
        raio_km: float
    ) -> List[float]:
        """
        Calcula bounding box aproximado ao redor de um ponto

        Args:
            latitude: Latitude central
            longitude: Longitude central
            raio_km: Raio em km

        Returns:
            list: [minLng, minLat, maxLng, maxLat]
        """
        # Conversão aproximada: 1 grau ≈ 111 km
        delta_lat = raio_km / 111.0
        delta_lng = raio_km / (111.0 * abs(latitude / 90.0)) if latitude != 0 else raio_km / 111.0

        return [
            longitude - delta_lng,  # minLng
            latitude - delta_lat,   # minLat
            longitude + delta_lng,  # maxLng
            latitude + delta_lat    # maxLat
        ]

    def verificar_alertas_proximos_ponto_panc(
        self,
        ponto_panc_id: int,
        raio_km: float = 5
    ) -> Dict:
        """
        Verifica alertas de desmatamento próximos a um ponto PANC específico

        Args:
            ponto_panc_id: ID do ponto PANC
            raio_km: Raio de busca em km

        Returns:
            dict: Informações sobre alertas próximos
        """
        from mapping.models import PontoPANC

        try:
            ponto = PontoPANC.objects.get(id=ponto_panc_id)

            if not ponto.localizacao:
                return {
                    'erro': 'Ponto não possui localização',
                    'alertas': []
                }

            latitude = ponto.localizacao.y
            longitude = ponto.localizacao.x

            # Busca alertas na região
            alertas_data = self.buscar_alertas(
                latitude=latitude,
                longitude=longitude,
                raio_km=raio_km,
                data_inicio=(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            )

            if not alertas_data:
                return {
                    'ponto_id': ponto_panc_id,
                    'ponto_nome': ponto.nome_popular,
                    'alertas': [],
                    'total_alertas': 0,
                    'area_total_desmatada_ha': 0
                }

            alertas = alertas_data.get('collection', [])
            area_total = sum(alerta.get('areaHa', 0) for alerta in alertas)

            return {
                'ponto_id': ponto_panc_id,
                'ponto_nome': ponto.nome_popular,
                'latitude': latitude,
                'longitude': longitude,
                'raio_busca_km': raio_km,
                'alertas': alertas,
                'total_alertas': len(alertas),
                'area_total_desmatada_ha': round(area_total, 2),
                'metadata': alertas_data.get('metadata', {})
            }

        except PontoPANC.DoesNotExist:
            return {
                'erro': 'Ponto PANC não encontrado',
                'alertas': []
            }
        except Exception as e:
            logger.error(f"Erro ao verificar alertas para ponto PANC {ponto_panc_id}: {e}")
            return {
                'erro': str(e),
                'alertas': []
            }


# Instância global do serviço
mapbiomas_service = MapBiomasService()
