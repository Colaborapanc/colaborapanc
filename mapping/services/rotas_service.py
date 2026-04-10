# mapping/services/rotas_service.py
# Serviço para cálculo de rotas otimizadas entre pontos PANC

import os
import logging
import requests
from typing import List, Dict, Tuple
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

logger = logging.getLogger(__name__)


class RotasService:
    """
    Serviço para cálculo de rotas otimizadas entre múltiplos pontos PANC
    """

    def __init__(self):
        # API Key do OpenRouteService (ou similar)
        self.api_key = os.environ.get('OPENROUTESERVICE_API_KEY', '')
        self.base_url = 'https://api.openrouteservice.org/v2'

    def calcular_rota_otimizada(self, pontos: List[Dict]) -> Dict:
        """
        Calcula rota otimizada para visitar múltiplos pontos

        Args:
            pontos: Lista de dicionários com 'id', 'lat', 'lng'

        Returns:
            dict: Dados da rota incluindo ordem, distância, tempo
        """
        if len(pontos) < 2:
            return {
                'error': 'É necessário pelo menos 2 pontos',
                'ordem_otimizada': [],
                'distancia_total': 0,
                'tempo_estimado': 0
            }

        # Se a API não estiver configurada, retorna ordem simples
        if not self.api_key:
            logger.warning("API de rotas não configurada. Usando ordem simples.")
            return self._calcular_rota_simples(pontos)

        try:
            # Usa OpenRouteService Optimization API
            return self._calcular_com_openrouteservice(pontos)

        except Exception as e:
            logger.error(f"Erro ao calcular rota otimizada: {e}")
            return self._calcular_rota_simples(pontos)

    def _calcular_com_openrouteservice(self, pontos: List[Dict]) -> Dict:
        """
        Calcula rota usando OpenRouteService Optimization API
        """
        # Prepara dados para a API
        jobs = []
        for i, ponto in enumerate(pontos):
            jobs.append({
                'id': ponto['id'],
                'location': [ponto['lng'], ponto['lat']],
                'service': 300  # 5 minutos de parada em cada ponto
            })

        # Veículo (caminhada ou carro)
        vehicles = [{
            'id': 1,
            'profile': 'driving-car',  # ou 'foot-walking'
            'start': [pontos[0]['lng'], pontos[0]['lat']],
            'end': [pontos[0]['lng'], pontos[0]['lat']]
        }]

        payload = {
            'jobs': jobs,
            'vehicles': vehicles
        }

        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f'{self.base_url}/optimization',
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            route = data['routes'][0]

            return {
                'ordem_otimizada': [step['job'] for step in route['steps'] if step['type'] == 'job'],
                'distancia_total': route['distance'] / 1000,  # metros para km
                'tempo_estimado': route['duration'] / 60,  # segundos para minutos
                'geometry': route.get('geometry', '')
            }
        else:
            logger.error(f"Erro na API OpenRouteService: {response.status_code}")
            return self._calcular_rota_simples(pontos)

    def _calcular_rota_simples(self, pontos: List[Dict]) -> Dict:
        """
        Calcula rota simples (vizinho mais próximo) sem API externa
        """
        if not pontos:
            return {
                'ordem_otimizada': [],
                'distancia_total': 0,
                'tempo_estimado': 0
            }

        # Algoritmo do vizinho mais próximo
        pontos_nao_visitados = pontos.copy()
        rota = []
        ponto_atual = pontos_nao_visitados.pop(0)
        rota.append(ponto_atual['id'])

        distancia_total = 0

        while pontos_nao_visitados:
            # Encontra ponto mais próximo
            ponto_mais_proximo = None
            menor_distancia = float('inf')

            for ponto in pontos_nao_visitados:
                dist = self._calcular_distancia_haversine(
                    ponto_atual['lat'], ponto_atual['lng'],
                    ponto['lat'], ponto['lng']
                )
                if dist < menor_distancia:
                    menor_distancia = dist
                    ponto_mais_proximo = ponto

            # Move para o próximo ponto
            rota.append(ponto_mais_proximo['id'])
            distancia_total += menor_distancia
            ponto_atual = ponto_mais_proximo
            pontos_nao_visitados.remove(ponto_mais_proximo)

        # Tempo estimado (assume velocidade média de 40 km/h)
        tempo_estimado = (distancia_total / 40) * 60  # minutos

        return {
            'ordem_otimizada': rota,
            'distancia_total': round(distancia_total, 2),
            'tempo_estimado': round(tempo_estimado, 0)
        }

    def _calcular_distancia_haversine(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> float:
        """
        Calcula distância entre dois pontos usando fórmula de Haversine

        Returns:
            float: Distância em km
        """
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Raio da Terra em km

        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def obter_pontos_proximos(
        self,
        latitude: float,
        longitude: float,
        raio_km: float = 10,
        limite: int = 10
    ) -> List[Dict]:
        """
        Obtém pontos PANC próximos a uma localização

        Args:
            latitude: Latitude do ponto central
            longitude: Longitude do ponto central
            raio_km: Raio de busca em km
            limite: Número máximo de pontos

        Returns:
            list: Lista de pontos próximos
        """
        from mapping.models import PontoPANC

        ponto_central = Point(longitude, latitude, srid=4326)

        pontos = PontoPANC.objects.filter(
            localizacao__distance_lte=(ponto_central, D(km=raio_km)),
            status_validacao='aprovado'
        ).select_related('planta')[:limite]

        resultado = []
        for ponto in pontos:
            if ponto.localizacao:
                resultado.append({
                    'id': ponto.id,
                    'nome': ponto.planta.nome_popular if ponto.planta else ponto.nome_popular,
                    'lat': ponto.localizacao.y,
                    'lng': ponto.localizacao.x,
                    'cidade': ponto.cidade,
                    'tipo_local': ponto.tipo_local
                })

        return resultado

    def sugerir_rota_automatica(
        self,
        latitude: float,
        longitude: float,
        num_pontos: int = 5,
        raio_km: float = 20
    ) -> Dict:
        """
        Sugere uma rota automática baseada em pontos próximos interessantes

        Args:
            latitude: Latitude inicial
            longitude: Longitude inicial
            num_pontos: Número de pontos desejados na rota
            raio_km: Raio máximo de busca

        Returns:
            dict: Dados da rota sugerida
        """
        # Obtém pontos próximos
        pontos_proximos = self.obter_pontos_proximos(
            latitude=latitude,
            longitude=longitude,
            raio_km=raio_km,
            limite=num_pontos
        )

        if not pontos_proximos:
            return {
                'error': 'Nenhum ponto encontrado na região',
                'pontos': []
            }

        # Calcula rota otimizada
        rota = self.calcular_rota_otimizada(pontos_proximos)

        return {
            'pontos': pontos_proximos,
            'rota': rota,
            'total_pontos': len(pontos_proximos)
        }


# Instância global do serviço
rotas_service = RotasService()
