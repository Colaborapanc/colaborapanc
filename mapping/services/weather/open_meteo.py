import os

from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class OpenMeteoService:
    name = "Open-Meteo"
    requires_token = False

    def __init__(self):
        self.base_url = os.environ.get("OPENMETEO_API_URL", "https://api.open-meteo.com/v1/forecast")
        self.client = ResilientHTTPClient(HTTPConfig(base_url=self.base_url, timeout_seconds=6, retries=1))

    def healthcheck(self):
        _, error = self.client.get_json("", params={"latitude": -23.55, "longitude": -46.63, "current": "temperature_2m"})
        return {"ok": error is None, "error": error, "endpoint": self.base_url}
