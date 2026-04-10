import logging
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from mapping.models import EventoMonitorado, PontoPANC
from .mapbiomas_alert_service import MapBiomasAlertService
from .nasa_firms_service import NASAFirmsService

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    errors: int = 0


class EnvironmentalMonitorService:
    def __init__(self):
        self.mapbiomas = MapBiomasAlertService()
        self.nasa = NASAFirmsService()

    def sync(
        self,
        ponto_id=None,
        fonte=None,
        days=None,
        raio=None,
        full=False,
        latest_only=False,
    ):
        radius = raio or settings.ALERT_MONITOR_RADIUS_METERS
        lookback_days = days or settings.ALERT_MONITOR_DEFAULT_DAYS
        pontos = PontoPANC.objects.filter(localizacao__isnull=False)
        if ponto_id:
            pontos = pontos.filter(id=ponto_id)

        result = SyncResult()
        for ponto in pontos.iterator():
            lat = ponto.localizacao.y
            lon = ponto.localizacao.x
            logger.info("Monitorando ponto=%s fonte=%s", ponto.id, fonte or "todas")

            if fonte in (None, "mapbiomas"):
                self._sync_provider(
                    provider_name="mapbiomas",
                    fetcher=lambda: self.mapbiomas.fetch_alerts(lat, lon, radius, lookback_days, full),
                    ponto=ponto,
                    result=result,
                    latest_only=latest_only,
                )

            if fonte in (None, "nasa_firms"):
                self._sync_provider(
                    provider_name="nasa_firms",
                    fetcher=lambda: self.nasa.fetch_events(lat, lon, radius, lookback_days, full),
                    ponto=ponto,
                    result=result,
                    latest_only=latest_only,
                )

        return result

    def _sync_provider(self, provider_name, fetcher, ponto, result: SyncResult, latest_only=False):
        try:
            events = fetcher() or []
            events = self._filtrar_janela_ultimo_ano(events)
            if latest_only and events:
                evento_mais_recente = max(events, key=lambda event: event.get("ocorrido_em") or timezone.now())
                events = [evento_mais_recente]
            for event in events:
                self._upsert_event(ponto, event, result)
            logger.info("Ponto=%s provider=%s eventos=%s", ponto.id, provider_name, len(events))
        except Exception:
            result.errors += 1
            logger.exception("Falha na sincronização do provider=%s para ponto=%s", provider_name, ponto.id)

    def _filtrar_janela_ultimo_ano(self, events):
        limite = timezone.now() - timedelta(days=365)
        filtrados = []
        for event in events:
            ocorrido_em = event.get("ocorrido_em") or timezone.now()
            if ocorrido_em >= limite:
                filtrados.append(event)
        return filtrados

    @transaction.atomic
    def _upsert_event(self, ponto, event, result: SyncResult):
        external_id = event.get("external_id") or event.get("hash_evento")
        defaults = {
            "tipo_evento": event["tipo_evento"],
            "hash_evento": event.get("hash_evento") or external_id,
            "titulo": event.get("titulo", ""),
            "descricao": event.get("descricao", ""),
            "ocorrido_em": event.get("ocorrido_em") or timezone.now(),
            "publicado_em": event.get("publicado_em"),
            "latitude_evento": event.get("latitude_evento"),
            "longitude_evento": event.get("longitude_evento"),
            "bbox": event.get("bbox"),
            "area_afetada_ha": event.get("area_afetada_ha"),
            "distancia_metros": event.get("distancia_metros"),
            "severidade": event.get("severidade", ""),
            "confianca": event.get("confianca", ""),
            "brilho": event.get("brilho"),
            "frp": event.get("frp"),
            "metadata": event.get("metadata") or {},
            "status_sync": "sincronizado",
        }

        if external_id:
            _, created = EventoMonitorado.objects.update_or_create(
                ponto=ponto,
                fonte=event["fonte"],
                external_id=external_id,
                ocorrido_em=defaults["ocorrido_em"],
                defaults=defaults,
            )
        else:
            obj = EventoMonitorado.objects.filter(
                ponto=ponto,
                fonte=event["fonte"],
                hash_evento=defaults["hash_evento"],
                ocorrido_em=defaults["ocorrido_em"],
            ).first()
            if obj:
                for field, value in defaults.items():
                    setattr(obj, field, value)
                obj.save(update_fields=list(defaults.keys()) + ["atualizado_em"])
                created = False
            else:
                EventoMonitorado.objects.create(
                    ponto=ponto,
                    fonte=event["fonte"],
                    external_id=external_id,
                    **defaults,
                )
                created = True

        if created:
            result.created += 1
        else:
            result.updated += 1
