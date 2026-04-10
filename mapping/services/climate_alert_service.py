import hashlib
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from mapping.models import AlertaClimatico, PontoPANC
from mapping.services.mapbiomas_alert_service import MapBiomasAlertService

logger = logging.getLogger(__name__)


@dataclass
class ProviderSyncStatus:
    provider: str
    ok: bool
    imported: int = 0
    error: str | None = None


@dataclass
class ClimateSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    provider_status: list[ProviderSyncStatus] = field(default_factory=list)


class ClimateAlertService:
    """Pipeline climático+ambiental único: INMET + Open-Meteo + MapBiomas."""

    DEFAULT_INMET_FEED = "https://apiprevmet3.inmet.gov.br/rss/alerta"
    DEFAULT_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

    def __init__(self):
        self.inmet_feed_url = getattr(settings, "INMET_ALERTS_FEED_URL", self.DEFAULT_INMET_FEED)
        self.open_meteo_url = getattr(settings, "OPENMETEO_API_URL", self.DEFAULT_OPEN_METEO)
        self.timeout = int(getattr(settings, "ALERT_MONITOR_TIMEOUT_SECONDS", 20))
        self.radius_meters = int(getattr(settings, "ALERT_MONITOR_RADIUS_METERS", 5000))
        self.mapbiomas = MapBiomasAlertService()

    def sync(self, *, ponto_id: int | None = None, only_active: bool = False) -> ClimateSyncResult:
        pontos = PontoPANC.objects.filter(localizacao__isnull=False)
        if ponto_id:
            pontos = pontos.filter(id=ponto_id)

        result = ClimateSyncResult()
        for ponto in pontos.iterator():
            normalized = self._collect_for_point(ponto, result)
            if only_active:
                now = timezone.now()
                normalized = [a for a in normalized if a["inicio"] <= now <= a["fim"]]
            try:
                self._upsert_alerts(ponto, normalized, result)
            except Exception as exc:
                result.errors += 1
                logger.exception("Erro ao persistir alertas para ponto=%s: %s", ponto.id, exc)

        self.expire_alerts()
        return result

    def _collect_for_point(self, ponto: PontoPANC, result: ClimateSyncResult) -> list[dict]:
        providers = [
            ("inmet", self._fetch_inmet_alerts),
            ("open_meteo", self._fetch_open_meteo_alerts),
            ("mapbiomas", self._fetch_mapbiomas_alerts),
        ]
        alerts: list[dict] = []
        for provider_name, fn in providers:
            try:
                current = fn(ponto)
                alerts.extend(current)
                result.provider_status.append(ProviderSyncStatus(provider=provider_name, ok=True, imported=len(current)))
            except Exception as exc:
                logger.warning("Coleta parcial indisponível provider=%s ponto=%s erro=%s", provider_name, ponto.id, exc)
                result.provider_status.append(ProviderSyncStatus(provider=provider_name, ok=False, imported=0, error=str(exc)))
        return self._deduplicate(alerts)

    def _fetch_inmet_alerts(self, ponto: PontoPANC) -> list[dict]:
        response = requests.get(self.inmet_feed_url, timeout=self.timeout)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        items = root.findall(".//item")

        normalized: list[dict] = []
        estado = (ponto.estado or "").strip().upper()
        cidade = (ponto.cidade or "").strip().lower()

        for item in items:
            title = (item.findtext("title") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub_date = self._parse_rfc822(item.findtext("pubDate")) or timezone.now()

            content = f"{title} {description}".lower()
            if not self._is_territorial_match(content, estado=estado, cidade=cidade):
                continue

            inicio = pub_date
            fim = inicio + timedelta(hours=24)
            tipo = self._infer_type(title, description)
            severidade = self._infer_severity(title, description)
            ext_id = self._build_external_id("INMET", title, inicio.isoformat(), estado, cidade)

            normalized.append(
                {
                    "tipo": tipo,
                    "descricao": description or title,
                    "severidade": severidade,
                    "inicio": inicio,
                    "fim": fim,
                    "municipio": ponto.cidade or "",
                    "uf": ponto.estado or "",
                    "id_alerta": ext_id,
                    "fonte": "INMET",
                }
            )
        return normalized

    def _fetch_open_meteo_alerts(self, ponto: PontoPANC) -> list[dict]:
        lat = ponto.localizacao.y
        lon = ponto.localizacao.x
        response = requests.get(
            self.open_meteo_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "precipitation,temperature_2m,windspeed_10m",
                "timezone": "America/Sao_Paulo",
                "forecast_days": 2,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        hourly = payload.get("hourly") or {}

        times = hourly.get("time") or []
        rain = hourly.get("precipitation") or []
        temp = hourly.get("temperature_2m") or []
        wind = hourly.get("windspeed_10m") or []

        normalized: list[dict] = []
        for idx, time_value in enumerate(times):
            dt = self._parse_dt(time_value)
            if not dt:
                continue
            precipitation = self._safe_value(rain, idx)
            temperature = self._safe_value(temp, idx)
            windspeed = self._safe_value(wind, idx)

            rules = [
                (precipitation is not None and precipitation >= 20, "Chuva forte", "alta", f"Precipitação prevista de {precipitation} mm/h."),
                (windspeed is not None and windspeed >= 60, "Vento forte", "alta", f"Vento previsto de {windspeed} km/h."),
                (temperature is not None and temperature >= 36, "Calor intenso", "media", f"Temperatura prevista de {temperature}°C."),
            ]
            for should_emit, tipo, sev, desc in rules:
                if not should_emit:
                    continue
                normalized.append(
                    {
                        "tipo": tipo,
                        "descricao": desc,
                        "severidade": sev,
                        "inicio": dt,
                        "fim": dt + timedelta(hours=3),
                        "municipio": ponto.cidade or "",
                        "uf": ponto.estado or "",
                        "id_alerta": self._build_external_id("OPEN_METEO", tipo, dt.isoformat(), ponto.id),
                        "fonte": "OPEN_METEO",
                    }
                )
        return normalized

    def _fetch_mapbiomas_alerts(self, ponto: PontoPANC) -> list[dict]:
        lat = ponto.localizacao.y
        lon = ponto.localizacao.x
        response = self.mapbiomas.fetch_alerts(
            latitude=lat,
            longitude=lon,
            radius_meters=self.radius_meters,
            days=int(getattr(settings, "ALERT_MONITOR_DEFAULT_DAYS", 7)),
            full=False,
        )
        normalized: list[dict] = []
        for item in response or []:
            inicio = item.get("ocorrido_em") or timezone.now()
            fim = inicio + timedelta(days=90)
            external_id = item.get("external_id") or self._build_external_id("MAPBIOMAS", inicio.isoformat(), ponto.id)
            normalized.append(
                {
                    "tipo": "Desmatamento",
                    "descricao": item.get("descricao") or "Supressão de vegetação detectada pelo MapBiomas.",
                    "severidade": self._normalize_severity(item.get("severidade")),
                    "inicio": inicio,
                    "fim": fim,
                    "municipio": ponto.cidade or "",
                    "uf": ponto.estado or "",
                    "id_alerta": str(external_id),
                    "fonte": "MAPBIOMAS",
                }
            )
        return normalized

    @transaction.atomic
    def _upsert_alerts(self, ponto: PontoPANC, alerts: list[dict], result: ClimateSyncResult) -> None:
        for payload in alerts:
            if payload["fim"] <= payload["inicio"]:
                result.skipped += 1
                continue
            _, created = AlertaClimatico.objects.update_or_create(
                ponto=ponto,
                tipo=payload["tipo"],
                inicio=payload["inicio"],
                fim=payload["fim"],
                defaults={
                    "descricao": payload.get("descricao", ""),
                    "severidade": payload.get("severidade", ""),
                    "municipio": payload.get("municipio", ""),
                    "uf": payload.get("uf", ""),
                    "id_alerta": payload.get("id_alerta", ""),
                    "fonte": payload.get("fonte", "INMET"),
                },
            )
            if created:
                result.created += 1
            else:
                result.updated += 1

    def expire_alerts(self) -> int:
        now = timezone.now()
        return AlertaClimatico.objects.filter(fim__lt=now).count()

    def get_active_alerts(self, *, ponto_id: int | None = None, limit: int = 200) -> list[AlertaClimatico]:
        now = timezone.now()
        qs = AlertaClimatico.objects.select_related("ponto").filter(inicio__lte=now, fim__gte=now)
        if ponto_id:
            qs = qs.filter(ponto_id=ponto_id)
        return list(qs.order_by("-inicio")[:limit])

    def get_history(self, *, ponto_id: int | None = None, limit: int = 500) -> list[AlertaClimatico]:
        qs = AlertaClimatico.objects.select_related("ponto").all()
        if ponto_id:
            qs = qs.filter(ponto_id=ponto_id)
        return list(qs.order_by("-inicio")[:limit])

    def _deduplicate(self, alerts: list[dict]) -> list[dict]:
        seen: set[str] = set()
        deduped: list[dict] = []
        for item in alerts:
            key = "|".join(
                [
                    str(item.get("fonte", "")),
                    str(item.get("id_alerta") or ""),
                    str(item.get("tipo", "")),
                    str(item.get("inicio", "")),
                    str(item.get("fim", "")),
                ]
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    @staticmethod
    def _safe_value(values: list, index: int):
        if index >= len(values):
            return None
        try:
            return float(values[index])
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_dt(value: str):
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        except Exception:
            return None

    @staticmethod
    def _parse_rfc822(value: str | None):
        if not value:
            return None
        try:
            dt = parsedate_to_datetime(value)
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        except Exception:
            return None

    @staticmethod
    def _build_external_id(*parts) -> str:
        raw = "|".join(str(p or "") for p in parts)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _is_territorial_match(content: str, *, estado: str, cidade: str) -> bool:
        if "brasil" in content:
            return True
        state_match = bool(estado and estado.lower() in content)
        city_match = bool(cidade and cidade in content)
        if estado and cidade:
            return state_match or city_match
        if estado:
            return state_match
        if cidade:
            return city_match
        return True

    @staticmethod
    def _infer_type(title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if "chuva" in text:
            return "Chuva forte"
        if "vento" in text:
            return "Vento forte"
        if "calor" in text:
            return "Calor intenso"
        if "seca" in text:
            return "Seca"
        return "Alerta meteorológico"

    @staticmethod
    def _infer_severity(title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if any(k in text for k in ["perigo", "grave", "extremo", "severo"]):
            return "alta"
        if any(k in text for k in ["atenção", "moderado", "moderada"]):
            return "media"
        return "baixa"

    @staticmethod
    def _normalize_severity(value: str | None) -> str:
        text = (value or "").strip().lower()
        if not text:
            return "media"
        if any(k in text for k in ["alto", "alta", "grave", "confirmado"]):
            return "alta"
        if any(k in text for k in ["baixo", "baixa", "leve"]):
            return "baixa"
        return "media"
