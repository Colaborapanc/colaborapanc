import os
from django.conf import settings


class PlantIdHealthService:
    def __init__(self):
        self.api_key = (getattr(settings, "PLANTID_API_KEY", "") or os.environ.get("PLANTID_API_KEY", "")).strip()
        self.base_url = os.environ.get("PLANTID_API_URL", "https://api.plant.id/v2").rstrip("/")

    def healthcheck(self) -> dict:
        """
        Plant.id (v2) does not expose a dedicated authenticated health endpoint in this
        service integration. To avoid false negatives (400 due to invalid image payload)
        and false positives, this check is intentionally configuration-only (no outbound POST).
        """
        if not self.api_key:
            return {
                "ok": False,
                "error": "missing_api_key",
                "error_type": "credencial_ausente",
                "endpoint": f"{self.base_url}/identify",
                "method": "CHECK",
            }

        return {
            "ok": False,
            "error": "verificacao_limitada",
            "error_type": "verificacao_limitada",
            "endpoint": f"{self.base_url}/identify",
            "method": "CHECK",
            "status_code": None,
            "response_summary": "verificacao_limitada",
            "response_excerpt": "Plant.id sem endpoint de healthcheck autenticado neste fluxo; nenhuma chamada externa foi executada.",
            "latency_ms": 0,
            "request_headers": {"Api-Key": "***"},
        }
