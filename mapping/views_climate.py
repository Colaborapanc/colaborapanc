from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from mapping.models import AlertaClimatico
from mapping.serializers import AlertaClimaticoSerializer
from mapping.services.climate_alert_service import ClimateAlertService
from mapping.services.integration_health import IntegrationHealthService


climate_service = ClimateAlertService()
integration_health = IntegrationHealthService()


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _serialize_alert(alerta: AlertaClimatico) -> dict:
    data = AlertaClimaticoSerializer(alerta).data
    now = timezone.now()
    data["status"] = "ativo" if alerta.inicio <= now <= alerta.fim else "expirado"
    data["ponto_id"] = alerta.ponto_id
    data["ponto_nome"] = alerta.ponto.nome_popular
    return data


@api_view(["GET"])
@permission_classes([AllowAny])
def api_alertas_ativos(request):
    ponto_id = request.GET.get("ponto_id")
    limit = max(1, min(_to_int(request.GET.get("limit"), 200), 1000))
    alerts = climate_service.get_active_alerts(
        ponto_id=_to_int(ponto_id, None) if str(ponto_id or "").isdigit() else None,
        limit=limit,
    )
    payload = [_serialize_alert(item) for item in alerts]
    return Response({"count": len(payload), "results": payload}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_historico_alertas(request):
    ponto_id = request.GET.get("ponto_id") or request.GET.get("ponto")
    limit = max(1, min(_to_int(request.GET.get("limit"), 500), 2000))
    alerts = climate_service.get_history(
        ponto_id=_to_int(ponto_id, None) if str(ponto_id or "").isdigit() else None,
        limit=limit,
    )
    payload = [_serialize_alert(item) for item in alerts]
    return Response({"count": len(payload), "results": payload}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_sincronizar_alertas_climaticos(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

    ponto_id = request.data.get("ponto_id")
    only_active = bool(request.data.get("only_active", False))
    result = climate_service.sync(
        ponto_id=_to_int(ponto_id, None) if str(ponto_id or "").isdigit() else None,
        only_active=only_active,
    )
    return Response(
        {
            "created": result.created,
            "updated": result.updated,
            "skipped": result.skipped,
            "errors": result.errors,
            "provider_status": [status.__dict__ for status in result.provider_status],
            "executed_at": timezone.now(),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_status_operacional_clima(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

    integrations = [item for item in integration_health.check_all() if item.get("tipo_integracao") in {"Clima", "Ambiental"}]
    now = timezone.now()
    metricas = AlertaClimatico.objects.aggregate(
        total=Count("id"),
        ativos=Count("id", filter=Q(inicio__lte=now, fim__gte=now)),
        expirados=Count("id", filter=Q(fim__lt=now)),
    )
    return Response({"integracoes": integrations, "metricas_alertas": metricas}, status=status.HTTP_200_OK)
