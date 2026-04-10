import csv
import hashlib
import io
import logging
from datetime import timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from django.utils import timezone

from .environmental_utils import build_bbox_from_point, haversine_distance_meters, parse_iso_datetime

logger = logging.getLogger(__name__)


class NASAFirmsService:
    def __init__(self):
        self.api_url = settings.NASA_FIRMS_API_URL.rstrip("/")
        self.map_key = (getattr(settings, "NASA_FIRMS_MAP_KEY", "") or "").strip()
        self.source = settings.NASA_FIRMS_SOURCE
        self.timeout = settings.ALERT_MONITOR_TIMEOUT_SECONDS

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    @property
    def configured(self) -> bool:
        return bool(self.map_key)

    def fetch_events(self, latitude, longitude, radius_meters, days=7, full=False):
        if not self.configured:
            logger.info("NASA FIRMS não configurada: variável NASA_FIRMS_MAP_KEY ausente.")
            return []

        bbox = build_bbox_from_point(latitude, longitude, radius_meters)
        days_value = 30 if full else max(1, min(days, 30))
        bbox_param = ",".join(str(v) for v in bbox)
        # formato oficial /api/area/csv/<MAP_KEY>/<SOURCE>/<bbox>/<days>
        url = f"{self.api_url}/{self.map_key}/{self.source}/{bbox_param}/{days_value}"

        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        reader = csv.DictReader(io.StringIO(response.text))
        normalized = []

        for row in reader:
            lat = self._to_float(row.get("latitude"))
            lng = self._to_float(row.get("longitude"))
            if lat is None or lng is None:
                continue

            ocorrido_em = self._parse_datetime(row)
            confidence = str(row.get("confidence") or "")
            brightness = self._to_float(row.get("brightness") or row.get("bright_ti4"))
            frp = self._to_float(row.get("frp"))
            tipo_evento = "incendio" if confidence.lower() in {"h", "high", "n"} else "foco_calor"

            external_seed = f"{self.source}|{lat}|{lng}|{ocorrido_em.isoformat()}"
            external_id = hashlib.sha1(external_seed.encode("utf-8")).hexdigest()
            distancia = haversine_distance_meters(latitude, longitude, lat, lng)

            normalized.append(
                {
                    "fonte": "nasa_firms",
                    "tipo_evento": tipo_evento,
                    "external_id": external_id,
                    "hash_evento": external_id,
                    "ocorrido_em": ocorrido_em,
                    "publicado_em": None,
                    "latitude_evento": lat,
                    "longitude_evento": lng,
                    "bbox": bbox,
                    "distancia_metros": distancia,
                    "area_afetada_ha": None,
                    "confianca": confidence,
                    "brilho": brightness,
                    "frp": frp,
                    "titulo": "Foco de calor detectado",
                    "descricao": "Evento detectado via NASA FIRMS.",
                    "metadata": row,
                }
            )
        return normalized

    def healthcheck(self) -> dict:
        endpoint = f"{self.api_url}/<MAP_KEY>/{self.source}/<bbox>/1"
        if not self.configured:
            return {
                "ok": False,
                "error": "missing_api_key",
                "error_type": "nao_configurada",
                "endpoint": endpoint,
                "status_code": None,
            }

        test_lat, test_lon = -14.2, -51.9
        test_radius = 5_000
        bbox = build_bbox_from_point(test_lat, test_lon, test_radius)
        bbox_param = ",".join(str(v) for v in bbox)
        url = f"{self.api_url}/{self.map_key}/{self.source}/{bbox_param}/1"
        try:
            response = self.session.get(url, timeout=self.timeout)
            status_code = response.status_code
            response.raise_for_status()
            rows = list(csv.DictReader(io.StringIO(response.text)))
            return {
                "ok": True,
                "error": None,
                "error_type": None,
                "status_code": status_code,
                "endpoint": endpoint,
                "message": "sem_eventos" if not rows else "ok",
            }
        except requests.Timeout as exc:
            return {"ok": False, "error": str(exc), "error_type": "timeout", "endpoint": endpoint}
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code in (401, 403):
                error_type = "auth_error"
            elif status_code == 404:
                error_type = "endpoint_error"
            else:
                error_type = "http_error"
            return {
                "ok": False,
                "error": f"http_{status_code}",
                "error_type": error_type,
                "status_code": status_code,
                "endpoint": endpoint,
            }
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc), "error_type": "endpoint_error", "endpoint": endpoint}

    def _parse_datetime(self, row):
        acq_date = row.get("acq_date")
        acq_time = str(row.get("acq_time") or "0000").zfill(4)
        iso = f"{acq_date}T{acq_time[:2]}:{acq_time[2:]}:00+00:00" if acq_date else None
        return parse_iso_datetime(iso) or (timezone.now() - timedelta(minutes=1))

    @staticmethod
    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
