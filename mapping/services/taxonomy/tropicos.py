import os
from typing import Any
import xml.etree.ElementTree as ET
from django.conf import settings

from mapping.services.enrichment.cache import EnrichmentCache
from mapping.services.enrichment.http import HTTPConfig, ResilientHTTPClient


class TropicosService:
    source_name = "tropicos"

    def __init__(self):
        self.api_key = (getattr(settings, "TROPICOS_API_KEY", "") or os.environ.get("TROPICOS_API_KEY", "")).strip()
        base_url = getattr(settings, "TROPICOS_API_URL", "") or os.environ.get("TROPICOS_API_URL", "https://services.tropicos.org")
        self.client = ResilientHTTPClient(
            HTTPConfig(
                base_url=base_url,
                timeout_seconds=float(os.environ.get("ENRICH_HTTP_TIMEOUT", "8")),
                retries=int(os.environ.get("ENRICH_HTTP_RETRIES", "2")),
            )
        )
        self.cache = EnrichmentCache(ttl_seconds=int(os.environ.get("ENRICH_CACHE_TTL_TROPICOS", str(3600 * 24))))

    @staticmethod
    def _xml_to_records(xml_payload: str) -> list[dict[str, Any]]:
        if not xml_payload:
            return []
        root = ET.fromstring(xml_payload)
        records: list[dict[str, Any]] = []
        for item in list(root):
            if not isinstance(item.tag, str):
                continue
            rec: dict[str, Any] = {}
            for child in list(item):
                key = (child.tag or "").split("}")[-1]
                rec[key] = (child.text or "").strip()
            if rec:
                records.append(rec)
        return records

    def _fetch_tropicos(self, path: str, *, params: dict[str, Any]) -> tuple[list | dict, str | None, str | None]:
        request = self.client.get_json_detailed(path, params={**params, "apikey": self.api_key, "format": "json"})
        payload = request.get("payload")
        if payload:
            return payload, request.get("error"), request.get("error_type")

        xml_request = self.client.get_text_detailed(path, params={**params, "apikey": self.api_key, "format": "xml"})
        xml_raw = xml_request.get("payload")
        if xml_raw:
            try:
                return self._xml_to_records(xml_raw), xml_request.get("error"), xml_request.get("error_type")
            except Exception:
                return {}, "xml_parse_error", "parse_error"
        return {}, request.get("error") or xml_request.get("error"), request.get("error_type") or xml_request.get("error_type")

    def resolve(self, scientific_name: str) -> dict[str, Any]:
        if not self.api_key:
            return {"ok": False, "error": "missing_api_key", "error_type": "credencial_ausente"}

        payload = {"name": scientific_name.strip()}
        cached = self.cache.get("tropicos", payload)
        if cached is not None:
            return cached

        search, error, error_type = self._fetch_tropicos("/Name/Search", params={"name": scientific_name, "type": "exact"})
        first = search[0] if isinstance(search, list) and search else {}
        name_id = first.get("NameId")
        if not name_id:
            result = {"ok": False, "error": error or "not_found", "error_type": error_type or "not_found", "raw": {"search": search}}
            self.cache.set("tropicos", payload, result)
            return result

        details, err_details, err_type_details = self._fetch_tropicos(f"/Name/{name_id}", params={})
        synonyms, err_syn, err_type_syn = self._fetch_tropicos(f"/Name/{name_id}/Synonyms", params={})
        accepted, err_acc, err_type_acc = self._fetch_tropicos(f"/Name/{name_id}/AcceptedNames", params={})

        result = {
            "ok": True,
            "error": error or err_details or err_syn or err_acc,
            "error_type": error_type or err_type_details or err_type_syn or err_type_acc,
            "nome_aceito": (accepted[0].get("ScientificName") if isinstance(accepted, list) and accepted else first.get("ScientificName", "")),
            "sinonimos": [item.get("ScientificName") for item in (synonyms if isinstance(synonyms, list) else []) if item.get("ScientificName")],
            "autoria": first.get("Author", ""),
            "fonte_taxonomica_primaria": "Tropicos",
            "fontes_taxonomicas_secundarias": ["Tropicos"],
            "distribuicao_resumida": first.get("Family", ""),
            "raw": {"search": first, "details": details, "synonyms": synonyms, "accepted": accepted},
            "method": "GET",
            "endpoint": f"{self.client.config.base_url}/Name/Search",
        }
        self.cache.set("tropicos", payload, result)
        return result
