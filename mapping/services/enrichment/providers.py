import os
from collections import Counter
from typing import Any

from mapping.utils.cache_keys import build_safe_cache_key

from .clients import APIClientConfig, CachedHTTPClient


class GlobalNamesVerifierProvider:
    def __init__(self):
        self.client = CachedHTTPClient(APIClientConfig(base_url=os.environ.get("GNAMES_API_URL", "https://verifier.globalnames.org/api/v1"), timeout=float(os.environ.get("ENRICH_TIMEOUT", "6")), cache_ttl=3600 * 24))

    def validate_name(self, scientific_name: str) -> dict[str, Any]:
        payload = self.client.get_json(
            "/verifications",
            params={"name": scientific_name},
            cache_key=build_safe_cache_key("gnv", scientific_name),
        )
        data = (payload.get("data") or [{}])[0] if isinstance(payload.get("data"), list) else {}
        best = (data.get("bestResult") or {}) if isinstance(data, dict) else {}
        return {
            "nome_cientifico_submetido": scientific_name,
            "nome_cientifico_validado": best.get("canonicalName") or scientific_name,
            "nome_aceito": best.get("currentName") or best.get("canonicalName") or scientific_name,
            "autoria": best.get("authorship") or "",
            "fonte_taxonomica_primaria": "Global Names Verifier",
            "grau": 0.9 if best else 0.4,
            "raw": payload,
        }


class TropicosProvider:
    def __init__(self):
        self.api_key = os.environ.get("TROPICOS_API_KEY", "")
        self.client = CachedHTTPClient(APIClientConfig(base_url=os.environ.get("TROPICOS_API_URL", "https://services.tropicos.org"), timeout=float(os.environ.get("ENRICH_TIMEOUT", "6")), cache_ttl=3600 * 24))

    def resolve(self, scientific_name: str) -> dict[str, Any]:
        if not self.api_key:
            return {}
        search = self.client.get_json(
            "/Name/Search",
            params={"name": scientific_name, "type": "exact", "apikey": self.api_key, "format": "json"},
            cache_key=build_safe_cache_key("tropicos-search", scientific_name),
        )
        first = search[0] if isinstance(search, list) and search else {}
        tropicos_id = first.get("NameId")
        if not tropicos_id:
            return {}

        synonyms = self.client.get_json(
            f"/Name/{tropicos_id}/Synonyms",
            params={"apikey": self.api_key, "format": "json"},
            cache_key=build_safe_cache_key("tropicos-syn", tropicos_id),
        )
        accepted = self.client.get_json(
            f"/Name/{tropicos_id}/AcceptedNames",
            params={"apikey": self.api_key, "format": "json"},
            cache_key=build_safe_cache_key("tropicos-acc", tropicos_id),
        )

        synonyms_list = [item.get("ScientificName") for item in synonyms if item.get("ScientificName")] if isinstance(synonyms, list) else []
        accepted_name = accepted[0].get("ScientificName") if isinstance(accepted, list) and accepted else first.get("ScientificName")

        return {
            "nome_aceito": accepted_name,
            "sinonimos": synonyms_list,
            "autoria": first.get("Author") or "",
            "fonte_taxonomica_primaria": "Tropicos",
            "fontes_secundarias": ["Tropicos"],
            "distribuicao_resumida": first.get("Family") or "",
            "raw": {"search": first, "synonyms": synonyms, "accepted": accepted},
        }


class GBIFProvider:
    def __init__(self):
        self.client = CachedHTTPClient(APIClientConfig(base_url=os.environ.get("GBIF_API_URL", "https://api.gbif.org/v1"), timeout=float(os.environ.get("ENRICH_TIMEOUT", "6")), cache_ttl=60 * 30))

    def fetch(self, scientific_name: str) -> dict[str, Any]:
        match = self.client.get_json(
            "/species/match",
            params={"name": scientific_name},
            cache_key=build_safe_cache_key("gbif-match", scientific_name),
        )
        species_key = match.get("speciesKey")
        occ_count = 0
        media = {}
        if species_key:
            occ = self.client.get_json(
                "/occurrence/search",
                params={"taxonKey": species_key, "limit": 0},
                cache_key=build_safe_cache_key("gbif-occ", species_key),
            )
            occ_count = int(occ.get("count") or 0)
            media_resp = self.client.get_json(
                "/occurrence/search",
                params={"taxonKey": species_key, "limit": 1, "mediaType": "StillImage"},
                cache_key=build_safe_cache_key("gbif-media", species_key),
            )
            results = media_resp.get("results") or []
            media = results[0] if results else {}

        return {
            "nome_cientifico_validado": match.get("scientificName") or scientific_name,
            "ocorrencias_gbif": occ_count,
            "distribuicao_resumida": match.get("kingdom") or "",
            "imagem_url": ((media.get("media") or [{}])[0] or {}).get("identifier", "") if media else "",
            "imagem_fonte": "GBIF" if media else "",
            "licenca_imagem": ((media.get("media") or [{}])[0] or {}).get("license", "") if media else "",
            "fontes_secundarias": ["GBIF"],
            "raw": {"match": match, "media": media},
        }


class INaturalistProvider:
    def __init__(self):
        self.client = CachedHTTPClient(APIClientConfig(base_url=os.environ.get("INAT_API_URL", "https://api.inaturalist.org/v1"), timeout=float(os.environ.get("ENRICH_TIMEOUT", "6")), cache_ttl=60 * 30))

    def fetch(self, scientific_name: str) -> dict[str, Any]:
        observations = self.client.get_json(
            "/observations",
            params={"taxon_name": scientific_name, "per_page": 30, "photos": True},
            cache_key=build_safe_cache_key("inat-observations", scientific_name),
        )
        results = observations.get("results") or []
        phenology = Counter([r.get("observed_on_details", {}).get("month") for r in results if r.get("observed_on_details", {}).get("month")])
        top_months = [str(month) for month, _ in phenology.most_common(3)]

        first_photo = {}
        if results:
            photos = results[0].get("photos") or []
            first_photo = photos[0] if photos else {}

        return {
            "ocorrencias_inaturalist": int(observations.get("total_results") or len(results)),
            "fenologia_observada": ", ".join(top_months),
            "imagem_url": first_photo.get("url", "") or "",
            "imagem_fonte": "iNaturalist" if first_photo else "",
            "licenca_imagem": first_photo.get("license_code", "") if first_photo else "",
            "fontes_secundarias": ["iNaturalist"],
            "raw": observations,
        }


class TrefleProvider:
    def __init__(self):
        self.token = os.environ.get("TREFLE_TOKEN", "")
        self.client = CachedHTTPClient(APIClientConfig(base_url=os.environ.get("TREFLE_API_URL", "https://trefle.io/api/v1"), timeout=float(os.environ.get("ENRICH_TIMEOUT", "6")), cache_ttl=3600 * 12))

    def fetch_optional(self, scientific_name: str) -> dict[str, Any]:
        if not self.token:
            return {}
        payload = self.client.get_json(
            "/plants/search",
            params={"q": scientific_name, "token": self.token},
            cache_key=build_safe_cache_key("trefle-search", scientific_name),
        )
        first = (payload.get("data") or [{}])[0]
        if not first:
            return {}
        return {
            "fontes_secundarias": ["Trefle (opcional)",],
            "dados_opcionais": {
                "slug": first.get("slug"),
                "observacoes": "Sugestão opcional, não usada como verdade taxonômica.",
            },
            "raw": payload,
        }
