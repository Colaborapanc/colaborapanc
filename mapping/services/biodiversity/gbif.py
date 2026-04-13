import os
from typing import Any

from mapping.services.enrichment.cache import EnrichmentCache
from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class GBIFService:
    source_name = "gbif"

    def __init__(self):
        self.client = ResilientHTTPClient(
            HTTPConfig(
                base_url=os.environ.get("GBIF_API_URL", "https://api.gbif.org/v1"),
                timeout_seconds=float(os.environ.get("ENRICH_HTTP_TIMEOUT", "8")),
                retries=int(os.environ.get("ENRICH_HTTP_RETRIES", "2")),
            )
        )
        self.cache = EnrichmentCache(ttl_seconds=int(os.environ.get("ENRICH_CACHE_TTL_GBIF", "3600")))

    def fetch(self, scientific_name: str) -> dict[str, Any]:
        payload = {"name": scientific_name.strip()}
        cached = self.cache.get("gbif", payload)
        if cached is not None:
            return cached

        req_match = self.client.get_json_detailed("/species/match", params={"name": scientific_name})
        match = req_match.get("payload") or {}
        error = req_match.get("error")
        species_key = match.get("speciesKey") if isinstance(match, dict) else None
        if not species_key:
            result = {"ok": False, "error": error or "not_found", "error_type": req_match.get("error_type") or "not_found", "raw": {"match": match}}
            self.cache.set("gbif", payload, result)
            return result

        req_occ = self.client.get_json_detailed("/occurrence/search", params={"taxonKey": species_key, "limit": 0})
        occ = req_occ.get("payload") or {}
        err_occ = req_occ.get("error")
        req_media = self.client.get_json_detailed(
            "/occurrence/search", params={"taxonKey": species_key, "limit": 1, "mediaType": "StillImage"}
        )
        media_resp = req_media.get("payload") or {}
        err_media = req_media.get("error")

        media_item = ((media_resp.get("results") or [{}])[0] or {}) if isinstance(media_resp, dict) else {}
        media_asset = ((media_item.get("media") or [{}])[0] or {}) if media_item else {}

        result = {
            "ok": True,
            "error": error or err_occ or err_media,
            "error_type": req_match.get("error_type") or req_occ.get("error_type") or req_media.get("error_type"),
            "nome_cientifico_validado": (match.get("scientificName") if isinstance(match, dict) else "") or scientific_name,
            "ocorrencias_gbif": int((occ.get("count") if isinstance(occ, dict) else 0) or 0),
            "distribuicao_resumida": (match.get("kingdom") if isinstance(match, dict) else "") or "",
            "imagem_url": media_asset.get("identifier", ""),
            "imagem_fonte": "GBIF" if media_asset else "",
            "licenca_imagem": media_asset.get("license", ""),
            "raw": {"match": match, "occ": occ, "media": media_resp},
        }
        self.cache.set("gbif", payload, result)
        return result
