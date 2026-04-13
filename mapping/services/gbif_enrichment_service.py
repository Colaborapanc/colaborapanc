"""
Serviço de enriquecimento via GBIF (Global Biodiversity Information Facility).
Documentação: https://techdocs.gbif.org/en/openapi/v1/registry
Endpoints usados:
  - /v1/species/match  (match de nome)
  - /v1/species/{key}  (detalhes da espécie)
  - /v1/occurrence/search  (ocorrências)
  - /v1/species/{key}/media  (imagens)
"""

import logging
import os

import requests
from django.core.cache import cache
from mapping.utils.cache_keys import build_safe_cache_key

logger = logging.getLogger(__name__)

GBIF_API_BASE = "https://api.gbif.org/v1"
CACHE_TTL = 60 * 60 * 12  # 12 horas


class GBIFEnrichmentService:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.timeout = float(os.environ.get("ENRICHMENT_API_TIMEOUT", "15"))
        self.user_agent = os.environ.get(
            "COLABORAPANC_HTTP_USER_AGENT",
            "ColaboraPANC/1.0 (+https://foodlens.com.br)",
        )

    def enrich(self, nome_cientifico: str) -> dict:
        """
        Enriquece dados de uma espécie via GBIF.
        Retorna dict com:
        - species_key: int
        - nome_cientifico: str
        - nome_aceito: str
        - reino, filo, classe, ordem, familia, genero: str
        - status_taxonomico: str
        - ocorrencias_total: int
        - distribuicao_paises: list[str]
        - imagens: list[dict{url, fonte, licenca}]
        - sucesso: bool
        - erro: str | None
        """
        nome_cientifico = (nome_cientifico or "").strip()
        if not nome_cientifico:
            return {"sucesso": False, "erro": "Nome científico vazio"}

        cache_key = build_safe_cache_key("gbif-enrich", nome_cientifico)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            # 1. Match de nome
            match = self._species_match(nome_cientifico)
            if not match or match.get("matchType") == "NONE":
                result = {"sucesso": False, "erro": "Espécie não encontrada no GBIF", "nome_submetido": nome_cientifico}
                cache.set(cache_key, result, 60 * 60)
                return result

            species_key = match.get("usageKey") or match.get("speciesKey")
            if not species_key:
                result = {"sucesso": False, "erro": "Chave de espécie ausente no GBIF", "nome_submetido": nome_cientifico}
                cache.set(cache_key, result, 60 * 60)
                return result

            # 2. Contagem de ocorrências
            occ_count = self._occurrence_count(species_key)

            # 3. Distribuição (países com ocorrências)
            countries = self._occurrence_countries(species_key)

            # 4. Imagens
            images = self._species_media(species_key)

            result = {
                "sucesso": True,
                "erro": None,
                "species_key": species_key,
                "nome_cientifico": match.get("scientificName") or "",
                "nome_aceito": match.get("species") or match.get("canonicalName") or "",
                "autoria": _extract_gbif_authorship(match),
                "reino": match.get("kingdom") or "",
                "filo": match.get("phylum") or "",
                "classe": match.get("class") or "",
                "ordem": match.get("order") or "",
                "familia": match.get("family") or "",
                "genero": match.get("genus") or "",
                "status_taxonomico": match.get("status") or "",
                "match_type": match.get("matchType") or "",
                "ocorrencias_total": occ_count,
                "distribuicao_paises": countries[:30],
                "imagens": images[:5],
            }
            cache.set(cache_key, result, CACHE_TTL)
            return result

        except requests.RequestException as exc:
            logger.warning("GBIF indisponível: %s", exc)
            return {"sucesso": False, "erro": f"Erro de rede: {exc}", "nome_submetido": nome_cientifico}

    def _species_match(self, nome: str) -> dict:
        url = f"{GBIF_API_BASE}/species/match"
        response = self.session.get(
            url, params={"name": nome}, timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        response.raise_for_status()
        return response.json() or {}

    def _occurrence_count(self, species_key: int) -> int:
        url = f"{GBIF_API_BASE}/occurrence/search"
        try:
            response = self.session.get(
                url, params={"speciesKey": species_key, "limit": 0},
                timeout=self.timeout, headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            return response.json().get("count", 0)
        except requests.RequestException:
            return 0

    def _occurrence_countries(self, species_key: int) -> list[str]:
        url = f"{GBIF_API_BASE}/occurrence/search"
        try:
            response = self.session.get(
                url, params={"speciesKey": species_key, "limit": 100, "facet": "country", "facetLimit": 30},
                timeout=self.timeout, headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            data = response.json()
            facets = data.get("facets") or []
            for facet in facets:
                if facet.get("field") == "COUNTRY":
                    return [c.get("name") or "" for c in (facet.get("counts") or []) if c.get("name")]
        except requests.RequestException:
            pass
        return []

    def _species_media(self, species_key: int) -> list[dict]:
        url = f"{GBIF_API_BASE}/species/{species_key}/media"
        try:
            response = self.session.get(
                url, params={"limit": 10}, timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            results = response.json().get("results") or []
            images = []
            for item in results:
                if item.get("type") != "StillImage":
                    continue
                identifier = item.get("identifier") or ""
                if not identifier:
                    continue
                images.append({
                    "url": identifier,
                    "fonte": item.get("publisher") or item.get("source") or "GBIF",
                    "licenca": item.get("license") or "",
                    "descricao": item.get("description") or "",
                })
            return images
        except requests.RequestException:
            return []


def _extract_gbif_authorship(match: dict) -> str:
    scientific = match.get("scientificName") or ""
    canonical = match.get("canonicalName") or ""
    if scientific and canonical and canonical in scientific:
        return scientific.replace(canonical, "").strip()
    return ""
