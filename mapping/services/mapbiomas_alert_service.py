import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from .environmental_utils import build_bbox_from_point, haversine_distance_meters, parse_iso_datetime

logger = logging.getLogger(__name__)


class MapBiomasAlertService:
    def __init__(self):
        self.api_url = settings.MAPBIOMAS_API_URL
        self.email = settings.MAPBIOMAS_EMAIL
        self.password = settings.MAPBIOMAS_PASSWORD
        self.timeout = settings.ALERT_MONITOR_TIMEOUT_SECONDS

    def _authenticate(self):
        if not self.email or not self.password:
            logger.warning("MapBiomas sem credenciais configuradas")
            return None

        mutation = """
        mutation SignIn($email: String!, $password: String!) {
          signIn(email: $email, password: $password) { token }
        }
        """
        resp = requests.post(
            self.api_url,
            json={"query": mutation, "variables": {"email": self.email, "password": self.password}},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        return (((payload or {}).get("data") or {}).get("signIn") or {}).get("token")

    def fetch_alerts(self, latitude, longitude, radius_meters, days=7, full=False):
        token = self._authenticate()
        if not token:
            return []

        start_date = (timezone.now() - timedelta(days=365 if full else days)).date().isoformat()
        end_date = timezone.now().date().isoformat()
        bbox = build_bbox_from_point(latitude, longitude, radius_meters)

        query = """
        query GetAlerts($startDate: BaseDate!, $endDate: BaseDate!, $boundingBox: [Float!], $limit: Int, $page: Int) {
          alerts(startDate: $startDate, endDate: $endDate, dateType: DetectedAt, boundingBox: $boundingBox, limit: $limit, page: $page) {
            collection {
              alertCode
              detectedAt
              publishedAt
              areaHa
              alertGeometry
              statusName
              crossedStates
              crossedCities
            }
          }
        }
        """
        resp = requests.post(
            self.api_url,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query,
                "variables": {
                    "startDate": start_date,
                    "endDate": end_date,
                    "boundingBox": bbox,
                    "limit": 200,
                    "page": 1,
                },
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        collection = ((((resp.json() or {}).get("data") or {}).get("alerts") or {}).get("collection") or [])

        normalized = []
        for item in collection:
            geometry = item.get("alertGeometry") or {}
            coords = None
            if geometry.get("coordinates") and isinstance(geometry.get("coordinates"), list):
                # geralmente Polygon -> usa primeiro vértice para distância aproximada
                try:
                    first = geometry["coordinates"][0][0]
                    coords = (float(first[1]), float(first[0]))
                except Exception:
                    coords = None
            event_lat = coords[0] if coords else None
            event_lng = coords[1] if coords else None
            distance = None
            if event_lat is not None and event_lng is not None:
                distance = haversine_distance_meters(latitude, longitude, event_lat, event_lng)

            normalized.append(
                {
                    "fonte": "mapbiomas",
                    "tipo_evento": "desmatamento",
                    "external_id": str(item.get("alertCode") or ""),
                    "ocorrido_em": parse_iso_datetime(item.get("detectedAt")) or timezone.now(),
                    "publicado_em": parse_iso_datetime(item.get("publishedAt")),
                    "latitude_evento": event_lat,
                    "longitude_evento": event_lng,
                    "bbox": bbox,
                    "distancia_metros": distance,
                    "area_afetada_ha": item.get("areaHa"),
                    "severidade": item.get("statusName") or "",
                    "titulo": "Alerta de desmatamento",
                    "descricao": "Evento de supressão de vegetação detectado pelo MapBiomas Alerta.",
                    "metadata": item,
                }
            )
        return normalized
