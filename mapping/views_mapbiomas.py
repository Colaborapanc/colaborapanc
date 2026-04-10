# mapping/views_mapbiomas.py
# Views para integração com a API MapBiomas Alerta

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
import logging

from .services.mapbiomas_service import mapbiomas_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def buscar_alertas_desmatamento(request):
    """
    Busca alertas de desmatamento na região especificada

    Query params:
        - latitude (float, opcional): Latitude do ponto central
        - longitude (float, opcional): Longitude do ponto central
        - raio_km (float, opcional): Raio de busca em km (padrão: 10)
        - data_inicio (str, opcional): Data inicial (YYYY-MM-DD)
        - data_fim (str, opcional): Data final (YYYY-MM-DD)
        - territorio_ids (list, opcional): IDs de territórios
        - limite (int, opcional): Número máximo de resultados (padrão: 100)
        - pagina (int, opcional): Número da página (padrão: 1)
    """
    try:
        # Extrai parâmetros da query
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        raio_km = float(request.GET.get('raio_km', 10))
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')
        limite = int(request.GET.get('limite', 100))
        pagina = int(request.GET.get('pagina', 1))

        # Converte território_ids se fornecido
        territorio_ids = None
        territorio_ids_param = request.GET.get('territorio_ids')
        if territorio_ids_param:
            try:
                territorio_ids = [int(id) for id in territorio_ids_param.split(',')]
            except ValueError:
                return Response(
                    {'erro': 'territorio_ids deve ser uma lista de números separados por vírgula'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Converte lat/lng se fornecidos
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return Response(
                    {'erro': 'latitude e longitude devem ser números válidos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            latitude = None
            longitude = None

        # Cria chave de cache baseada nos parâmetros
        cache_key = f'mapbiomas_alertas_{latitude}_{longitude}_{raio_km}_{data_inicio}_{data_fim}_{pagina}'

        # Tenta obter do cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Retornando alertas do cache: {cache_key}")
            return Response(cached_result)

        # Busca alertas
        resultado = mapbiomas_service.buscar_alertas(
            latitude=latitude,
            longitude=longitude,
            raio_km=raio_km,
            data_inicio=data_inicio,
            data_fim=data_fim,
            territorio_ids=territorio_ids,
            limite=limite,
            pagina=pagina
        )

        if resultado is None:
            return Response(
                {'erro': 'Não foi possível buscar alertas. Verifique as credenciais da API.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Armazena no cache por 1 hora
        cache.set(cache_key, resultado, 60 * 60)

        return Response(resultado)

    except Exception as e:
        logger.error(f"Erro ao buscar alertas MapBiomas: {e}")
        return Response(
            {'erro': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def buscar_alerta_detalhado(request, alert_code):
    """
    Busca informações detalhadas de um alerta específico

    Args:
        alert_code (str): Código do alerta MapBiomas
    """
    try:
        # Verifica cache
        cache_key = f'mapbiomas_alerta_{alert_code}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        resultado = mapbiomas_service.buscar_alerta_detalhado(alert_code)

        if resultado is None:
            return Response(
                {'erro': 'Alerta não encontrado ou erro na API'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cache por 24 horas (dados de alerta não mudam com frequência)
        cache.set(cache_key, resultado, 24 * 60 * 60)

        return Response(resultado)

    except Exception as e:
        logger.error(f"Erro ao buscar alerta detalhado {alert_code}: {e}")
        return Response(
            {'erro': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def buscar_territorios(request):
    """
    Busca territórios disponíveis (biomas, municípios, UCs, etc.)

    Query params:
        - categoria (str, opcional): Categoria do território (BIOME, MUNICIPALITY, etc.)
        - nome (str, opcional): Nome do território para busca
        - limite (int, opcional): Número máximo de resultados (padrão: 100)
    """
    try:
        categoria = request.GET.get('categoria')
        nome = request.GET.get('nome')
        limite = int(request.GET.get('limite', 100))

        # Cache key
        cache_key = f'mapbiomas_territorios_{categoria}_{nome}_{limite}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        resultado = mapbiomas_service.buscar_territorios(
            categoria=categoria,
            nome=nome,
            limite=limite
        )

        if resultado is None:
            return Response(
                {'erro': 'Não foi possível buscar territórios'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Cache por 7 dias (territórios mudam raramente)
        cache.set(cache_key, resultado, 7 * 24 * 60 * 60)

        return Response(resultado)

    except Exception as e:
        logger.error(f"Erro ao buscar territórios MapBiomas: {e}")
        return Response(
            {'erro': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def buscar_alertas_propriedade(request):
    """
    Busca alertas associados a uma propriedade rural específica (CAR)

    Query params:
        - car_code (str, obrigatório): Código CAR da propriedade
        - data_inicio (str, opcional): Data inicial (YYYY-MM-DD)
        - data_fim (str, opcional): Data final (YYYY-MM-DD)
    """
    try:
        car_code = request.GET.get('car_code')

        if not car_code:
            return Response(
                {'erro': 'car_code é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')

        # Cache
        cache_key = f'mapbiomas_propriedade_{car_code}_{data_inicio}_{data_fim}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        resultado = mapbiomas_service.buscar_alertas_por_propriedade(
            car_code=car_code,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        if resultado is None:
            return Response(
                {'erro': 'Não foi possível buscar alertas da propriedade'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Cache por 6 horas
        cache.set(cache_key, resultado, 6 * 60 * 60)

        return Response(resultado)

    except Exception as e:
        logger.error(f"Erro ao buscar alertas de propriedade: {e}")
        return Response(
            {'erro': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def informacoes_ponto(request):
    """
    Obtém informações sobre alertas e territórios em um ponto específico

    Query params:
        - latitude (float, obrigatório): Latitude do ponto
        - longitude (float, obrigatório): Longitude do ponto
    """
    try:
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')

        if not latitude or not longitude:
            return Response(
                {'erro': 'latitude e longitude são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return Response(
                {'erro': 'latitude e longitude devem ser números válidos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cache
        cache_key = f'mapbiomas_ponto_{latitude}_{longitude}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        resultado = mapbiomas_service.obter_informacoes_ponto(
            latitude=latitude,
            longitude=longitude
        )

        if resultado is None:
            return Response(
                {'erro': 'Não foi possível obter informações do ponto'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Cache por 24 horas
        cache.set(cache_key, resultado, 24 * 60 * 60)

        return Response(resultado)

    except Exception as e:
        logger.error(f"Erro ao obter informações do ponto: {e}")
        return Response(
            {'erro': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verificar_alertas_ponto_panc(request, ponto_id):
    """
    Verifica alertas de desmatamento próximos a um ponto PANC específico

    Args:
        ponto_id (int): ID do ponto PANC

    Query params:
        - raio_km (float, opcional): Raio de busca em km (padrão: 5)
    """
    try:
        raio_km = float(request.GET.get('raio_km', 5))

        # Cache
        cache_key = f'mapbiomas_panc_{ponto_id}_{raio_km}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        resultado = mapbiomas_service.verificar_alertas_proximos_ponto_panc(
            ponto_panc_id=ponto_id,
            raio_km=raio_km
        )

        # Cache por 3 horas
        cache.set(cache_key, resultado, 3 * 60 * 60)

        return Response(resultado)

    except Exception as e:
        logger.error(f"Erro ao verificar alertas do ponto PANC {ponto_id}: {e}")
        return Response(
            {'erro': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def testar_conexao(request):
    """
    Testa a conexão com a API MapBiomas e retorna status
    """
    try:
        token = mapbiomas_service._get_token()

        if token:
            return Response({
                'status': 'sucesso',
                'mensagem': 'Conexão com MapBiomas estabelecida com sucesso',
                'autenticado': True
            })
        else:
            return Response({
                'status': 'erro',
                'mensagem': 'Não foi possível autenticar na API MapBiomas. Verifique as credenciais.',
                'autenticado': False
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    except Exception as e:
        logger.error(f"Erro ao testar conexão MapBiomas: {e}")
        return Response({
            'status': 'erro',
            'mensagem': str(e),
            'autenticado': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
