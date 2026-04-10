import os
from collections import Counter
from typing import Any

from mapping.services.enrichment.cache import EnrichmentCache
from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class INaturalistService:
    source_name = "inaturalist"

    def __init__(self):
        self.client = ResilientHTTPClient(
            HTTPConfig(
                base_url=os.environ.get("INAT_API_URL", "https://api.inaturalist.org/v1"),
                timeout_seconds=float(os.environ.get("ENRICH_HTTP_TIMEOUT", "8")),
                retries=int(os.environ.get("ENRICH_HTTP_RETRIES", "2")),
            )
        )
        self.cache = EnrichmentCache(ttl_seconds=int(os.environ.get("ENRICH_CACHE_TTL_INAT", "3600")))

    def fetch(self, scientific_name: str) -> dict[str, Any]:
        payload = {"name": scientific_name.strip()}
        cached = self.cache.get("inat", payload)
        if cached is not None:
            return cached

        req_obs = self.client.get_json_detailed(
            "/observations",
            params={"taxon_name": scientific_name, "per_page": 30, "photos": True, "order_by": "created_at"},
        )
        obs = req_obs.get("payload") or {}
        error = req_obs.get("error")
        results = obs.get("results") if isinstance(obs, dict) else []
        if not results:
            result = {"ok": False, "error": error or "not_found", "error_type": req_obs.get("error_type") or "not_found", "raw": obs}
            self.cache.set("inat", payload, result)
            return result

        month_counter = Counter([
            item.get("observed_on_details", {}).get("month")
            for item in results
            if item.get("observed_on_details", {}).get("month")
        ])
        top_months = [str(month) for month, _ in month_counter.most_common(6)]
        first_photo = (results[0].get("photos") or [{}])[0]

        result = {
            "ok": True,
            "error": error,
            "error_type": req_obs.get("error_type"),
            "ocorrencias_inaturalist": int(obs.get("total_results") or len(results)),
            "fenologia_observada": ", ".join(top_months),
            "fruit_months": top_months,
            "imagem_url": first_photo.get("url", ""),
            "imagem_fonte": "iNaturalist" if first_photo.get("url") else "",
            "licenca_imagem": first_photo.get("license_code", ""),
            "raw": obs,
        }
        self.cache.set("inat", payload, result)
        return result
