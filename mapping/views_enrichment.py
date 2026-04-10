"""
Endpoints da API de enriquecimento taxonômico.

Endpoints:
  POST /api/enriquecimento/            - Enriquecer por nome científico (cadastro)
  POST /api/enriquecimento/revalidar/  - Revalidar planta existente
  GET  /api/enriquecimento/<planta_id>/ - Consultar enriquecimento de uma planta
  GET  /api/enriquecimento/<planta_id>/historico/ - Histórico de enriquecimentos
"""

import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from mapping.models import PlantaReferencial, HistoricoEnriquecimento
from mapping.serializers import (
    EnriquecimentoPlantaSerializer,
    EnriquecimentoRequestSerializer,
    EnriquecimentoResponseSerializer,
    HistoricoEnriquecimentoSerializer,
)
from mapping.services.enrichment_orchestrator import EnrichmentOrchestrator

logger = logging.getLogger(__name__)

_orchestrator = EnrichmentOrchestrator()


@api_view(["POST"])
@permission_classes([AllowAny])
def enriquecer_nome(request):
    """
    Enriquece um nome científico usando todas as APIs configuradas.
    Aceita opcionalmente planta_id para vincular a uma PlantaReferencial existente.

    POST /api/enriquecimento/
    Body: {"nome_cientifico": "Pereskia aculeata", "planta_id": 123}
    """
    serializer = EnriquecimentoRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    nome_cientifico = serializer.validated_data["nome_cientifico"]
    planta_id = serializer.validated_data.get("planta_id")
    planta = None

    if planta_id:
        try:
            planta = PlantaReferencial.objects.get(pk=planta_id)
        except PlantaReferencial.DoesNotExist:
            return Response(
                {"erro": f"Planta com id={planta_id} não encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

    usuario = request.user if request.user.is_authenticated else None

    try:
        resultado = _orchestrator.enrich(
            nome_cientifico=nome_cientifico,
            planta=planta,
            usuario=usuario,
        )
    except Exception as exc:
        logger.exception("Erro no enriquecimento: %s", exc)
        return Response(
            {"erro": f"Erro interno no enriquecimento: {exc}", "sucesso": False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    resultado["sucesso"] = resultado.get("status") != "erro"
    return Response(resultado, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revalidar_planta(request):
    """
    Revalida uma planta existente executando novamente o pipeline de enriquecimento.

    POST /api/enriquecimento/revalidar/
    Body: {"planta_id": 123}
    """
    planta_id = request.data.get("planta_id")
    if not planta_id:
        return Response(
            {"erro": "planta_id é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        planta = PlantaReferencial.objects.get(pk=planta_id)
    except PlantaReferencial.DoesNotExist:
        return Response(
            {"erro": f"Planta com id={planta_id} não encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    nome_cientifico = planta.nome_cientifico or planta.nome_cientifico_valido or planta.nome_popular
    if not nome_cientifico:
        return Response(
            {"erro": "Planta não possui nome científico para revalidar"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        resultado = _orchestrator.enrich(
            nome_cientifico=nome_cientifico,
            planta=planta,
            usuario=request.user,
        )
    except Exception as exc:
        logger.exception("Erro na revalidação: %s", exc)
        return Response(
            {"erro": f"Erro interno na revalidação: {exc}", "sucesso": False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    resultado["sucesso"] = resultado.get("status") != "erro"
    return Response(resultado, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def consultar_enriquecimento(request, planta_id):
    """
    Consulta os dados de enriquecimento de uma planta.

    GET /api/enriquecimento/<planta_id>/
    """
    try:
        planta = PlantaReferencial.objects.get(pk=planta_id)
    except PlantaReferencial.DoesNotExist:
        return Response(
            {"erro": f"Planta com id={planta_id} não encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = EnriquecimentoPlantaSerializer(planta)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def historico_enriquecimento(request, planta_id):
    """
    Retorna histórico de enriquecimentos de uma planta.

    GET /api/enriquecimento/<planta_id>/historico/
    """
    try:
        planta = PlantaReferencial.objects.get(pk=planta_id)
    except PlantaReferencial.DoesNotExist:
        return Response(
            {"erro": f"Planta com id={planta_id} não encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    historicos = HistoricoEnriquecimento.objects.filter(planta=planta).order_by("-data")[:20]
    serializer = HistoricoEnriquecimentoSerializer(historicos, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
