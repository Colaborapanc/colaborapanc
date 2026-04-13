from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from mapping.services.mobile_parity_service import MobileParityService

service = MobileParityService()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def identificar_imagem_mobile(request):
    imagem = request.FILES.get("imagem") or request.FILES.get("foto")
    if not imagem:
        return Response({"erro": "Imagem não enviada"}, status=status.HTTP_400_BAD_REQUEST)

    usar_custom_db = str(request.data.get("usar_custom_db", "true")).lower() in {"true", "1", "sim"}
    usar_google = str(request.data.get("usar_google", "true")).lower() in {"true", "1", "sim"}
    resultado = service.identificar_por_imagem(
        imagem,
        usar_custom_db=usar_custom_db,
        usar_google=usar_google,
    )
    return Response(resultado.payload, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mapa_previews_mobile(request):
    termo = request.query_params.get("q") or ""
    limite = int(request.query_params.get("limite", 400))
    itens = service.listar_previews_mapa(termo=termo, limite=min(limite, 1000))
    return Response({"total": len(itens), "resultados": itens}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def offline_base_metadata_mobile(request):
    return Response(service.metadata_base_offline(), status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def offline_base_download_mobile(request):
    limite = int(request.query_params.get("limite", 500))
    busca = request.query_params.get("busca") or None
    payload = service.exportar_base_offline(limite=min(limite, 2000), busca=busca)
    return Response(payload, status=status.HTTP_200_OK)
