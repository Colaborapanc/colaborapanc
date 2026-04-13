import math
from datetime import datetime
from django.utils import timezone

EARTH_RADIUS_METERS = 6371000


def build_bbox_from_point(latitude: float, longitude: float, radius_meters: float):
    """Retorna bbox no formato [min_lng, min_lat, max_lng, max_lat]."""
    if radius_meters <= 0:
        return [longitude, latitude, longitude, latitude]

    lat_delta = (radius_meters / EARTH_RADIUS_METERS) * (180.0 / math.pi)
    cos_lat = math.cos(math.radians(latitude)) or 1e-9
    lng_delta = (radius_meters / EARTH_RADIUS_METERS) * (180.0 / math.pi) / cos_lat

    return [
        longitude - lng_delta,
        latitude - lat_delta,
        longitude + lng_delta,
        latitude + lat_delta,
    ]


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distância entre coordenadas em metros."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_METERS * c


def parse_iso_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return timezone.make_aware(value) if timezone.is_naive(value) else value

    candidate = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
    except ValueError:
        return None
