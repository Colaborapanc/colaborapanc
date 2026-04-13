import os
from typing import Any
from django.conf import settings

from mapping.services.enrichment.cache import EnrichmentCache
from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class TrefleTraitsService:
    source_name = "trefle"

    def __init__(self):
        self.token = (
            getattr(settings, "TREFLE_API_TOKEN", "")
            or getattr(settings, "TREFLE_TOKEN", "")
            or os.environ.get("TREFLE_API_TOKEN", "")
            or os.environ.get("TREFLE_TOKEN", "")
        ).strip()
        base_url = getattr(settings, "TREFLE_API_URL", "") or os.environ.get("TREFLE_API_URL", "https://trefle.io/api/v1")
        self.client = ResilientHTTPClient(
            HTTPConfig(
                base_url=base_url,
                timeout_seconds=float(os.environ.get("ENRICH_HTTP_TIMEOUT", "8")),
                retries=int(os.environ.get("ENRICH_HTTP_RETRIES", "2")),
            )
        )
        self.cache = EnrichmentCache(ttl_seconds=int(os.environ.get("ENRICH_CACHE_TTL_TREFLE", str(3600 * 12))))

    def fetch_optional_traits(self, scientific_name: str) -> dict[str, Any]:
        if not self.token:
            return {"ok": False, "error": "missing_api_key", "error_type": "credencial_ausente"}

        payload = {"name": scientific_name.strip()}
        cached = self.cache.get("trefle", payload)
        if cached is not None:
            return cached

        req_search = self.client.get_json_detailed("/plants/search", params={"q": scientific_name, "token": self.token})
        response = req_search.get("payload") or {}
        error = req_search.get("error")
        data = response.get("data") if isinstance(response, dict) else []
        first = data[0] if data else {}
        if not first:
            result = {"ok": False, "error": error or "not_found", "error_type": req_search.get("error_type") or "not_found", "raw": response}
            self.cache.set("trefle", payload, result)
            return result

        plant_id = first.get("id")
        req_details = self.client.get_json_detailed(f"/plants/{plant_id}", params={"token": self.token}) if plant_id else {"payload": {}, "error": None, "error_type": None}
        details = req_details.get("payload") or {}
        err_details = req_details.get("error")
        detail_data = details.get("data") if isinstance(details, dict) else {}
        detail_data = detail_data if isinstance(detail_data, dict) else {}
        growth = detail_data.get("growth") or {}
        if not isinstance(growth, dict):
            growth = {}
        specifications = detail_data.get("specifications") or {}
        if not isinstance(specifications, dict):
            specifications = {}
        images = detail_data.get("images") or []
        if isinstance(images, dict):
            images = [images]
        if not isinstance(images, list):
            images = []
        edible_part = detail_data.get("edible_part") or detail_data.get("edible_parts") or []
        if isinstance(edible_part, str):
            edible_part = [edible_part]
        if not isinstance(edible_part, list):
            edible_part = []

        fruit_months = growth.get("fruit_months") or []
        growth_months = growth.get("growth_months") or []
        bloom_months = growth.get("bloom_months") or []
        if not isinstance(fruit_months, list):
            fruit_months = []
        if not isinstance(growth_months, list):
            growth_months = []
        if not isinstance(bloom_months, list):
            bloom_months = []

        result = {
            "ok": True,
            "error": error or err_details,
            "error_type": req_search.get("error_type") or req_details.get("error_type"),
            "comestivel": detail_data.get("edible"),
            "edible_part": edible_part,
            "fruit_months": fruit_months,
            "growth_months": growth_months,
            "bloom_months": bloom_months,
            "days_to_harvest": growth.get("days_to_harvest"),
            "planting_days_to_harvest": growth.get("planting_days_to_harvest"),
            "toxicity": specifications.get("toxicity"),
            "main_image_url": ((images[0] or {}).get("image_url") if images else None),
            "raw": {"search": first, "details": detail_data},
            "method": req_search.get("method"),
            "status_code": req_search.get("status_code"),
            "endpoint": req_search.get("url"),
            "response_summary": req_search.get("response_summary"),
            "response_excerpt": req_search.get("response_excerpt"),
        }
        self.cache.set("trefle", payload, result)
        return result
