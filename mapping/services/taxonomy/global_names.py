import os
from typing import Any
from django.conf import settings

from mapping.services.enrichment.cache import EnrichmentCache
from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class GlobalNamesService:
    source_name = "global_names_verifier"

    def __init__(self):
        base_url = getattr(settings, "GNAMES_API_URL", "") or os.environ.get("GNAMES_API_URL", "https://verifier.globalnames.org/api/v1")
        self.client = ResilientHTTPClient(
            HTTPConfig(
                base_url=base_url,
                timeout_seconds=float(os.environ.get("ENRICH_HTTP_TIMEOUT", "8")),
                retries=int(os.environ.get("ENRICH_HTTP_RETRIES", "2")),
            )
        )
        self.cache = EnrichmentCache(ttl_seconds=int(os.environ.get("ENRICH_CACHE_TTL_GNV", str(3600 * 24))))

    @staticmethod
    def _extract_best_candidate(response: Any) -> tuple[dict[str, Any], str | None]:
        records: list[Any] = []
        if isinstance(response, dict):
            for key in ("data", "verifications", "results", "names"):
                value = response.get(key)
                if isinstance(value, list):
                    records = value
                    break
            if not records and any(k in response for k in ("bestResult", "canonicalName", "currentName")):
                records = [response]
        elif isinstance(response, list):
            records = response

        if not records:
            return {}, "response_empty"

        first = records[0] if isinstance(records[0], dict) else {}
        if not first:
            return {}, "schema_error"

        best = first.get("bestResult") if isinstance(first.get("bestResult"), dict) else first
        if not isinstance(best, dict):
            best = {}
        if not best and isinstance(first.get("results"), list):
            inner = first.get("results") or []
            best = inner[0] if inner and isinstance(inner[0], dict) else {}
        if not best and isinstance(first.get("name"), dict):
            best = first.get("name") or {}
        if not isinstance(best, dict):
            return {}, "schema_error"
        if not (best.get("canonicalName") or best.get("currentName") or best.get("scientificName") or best.get("name")):
            return {}, "schema_error"
        return best, None

    def validate_name(self, scientific_name: str) -> dict[str, Any]:
        clean_name = (scientific_name or "").strip()
        payload = {"name": clean_name}
        cached = self.cache.get("gnv", payload)
        if cached is not None:
            return cached

        request = self.client.post_json_detailed(
            "/verifications",
            json_body={"nameStrings": [clean_name], "withContext": True},
        )
        response = request.get("payload") or {}
        error = request.get("error")
        error_type = request.get("error_type")
        best, extraction_error = self._extract_best_candidate(response)
        result = {
            "ok": bool(best),
            "error": error or extraction_error,
            "error_type": error_type or extraction_error,
            "nome_cientifico_submetido": scientific_name,
            "nome_cientifico_validado": best.get("canonicalName") or best.get("scientificName") or best.get("name") or scientific_name,
            "nome_aceito": best.get("currentName") or best.get("canonicalName") or best.get("scientificName") or scientific_name,
            "autoria": best.get("authorship") or "",
            "fonte_taxonomica_primaria": "Global Names Verifier",
            "raw": response,
            "method": request.get("method"),
            "status_code": request.get("status_code"),
            "response_summary": request.get("response_summary"),
            "response_excerpt": request.get("response_excerpt"),
            "http_meta": {
                "status_code": request.get("status_code"),
                "latency_ms": request.get("latency_ms"),
                "url": request.get("url"),
                "method": request.get("method"),
            },
        }
        self.cache.set("gnv", payload, result)
        return result
