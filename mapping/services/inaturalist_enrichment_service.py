"""
Serviço de enriquecimento via iNaturalist API.
Endpoints:
  - /v1/taxa  (busca de taxon)
  - /v1/observations  (observações com fenologia)
  - /v1/observations/species_counts  (contagens)
"""

import logging
import os
from collections import Counter

import requests
from django.core.cache import cache
from mapping.utils.cache_keys import build_safe_cache_key

logger = logging.getLogger(__name__)

INATURALIST_API_BASE = "https://api.inaturalist.org/v1"
CACHE_TTL = 60 * 60 * 6  # 6 horas


class INaturalistEnrichmentService:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.timeout = float(os.environ.get("ENRICHMENT_API_TIMEOUT", "15"))
        self.user_agent = os.environ.get(
            "COLABORAPANC_HTTP_USER_AGENT",
            "ColaboraPANC/1.0 (+https://foodlens.com.br)",
        )

    def enrich(self, nome_cientifico: str) -> dict:
        """
        Enriquece com dados do iNaturalist: observações, fenologia, imagens.
        Retorna dict com:
        - taxon_id: int
        - nome_cientifico: str
        - nome_popular: str
        - ocorrencias_total: int
        - fenologia: dict{meses: dict[str,int], estacao_pico: str}
        - imagens: list[dict{url, atribuicao, licenca}]
        - observacao_mais_recente: str (data)
        - sucesso: bool
        - erro: str | None
        """
        nome_cientifico = (nome_cientifico or "").strip()
        if not nome_cientifico:
            return {"sucesso": False, "erro": "Nome científico vazio"}

        cache_key = build_safe_cache_key("inat-enrich", nome_cientifico)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            # 1. Buscar taxon
            taxon = self._search_taxon(nome_cientifico)
            if not taxon:
                result = {"sucesso": False, "erro": "Taxon não encontrado no iNaturalist", "nome_submetido": nome_cientifico}
                cache.set(cache_key, result, 60 * 60)
                return result

            taxon_id = taxon.get("id")

            # 2. Contagem de observações
            obs_count = self._observation_count(taxon_id)

            # 3. Fenologia (meses das observações)
            fenologia = self._compute_phenology(taxon_id)

            # 4. Imagens das observações
            images = self._observation_photos(taxon_id)

            # 5. Foto padrão do taxon
            default_photo = taxon.get("default_photo") or {}
            if default_photo.get("medium_url") and not any(i["url"] == default_photo["medium_url"] for i in images):
                images.insert(0, {
                    "url": default_photo.get("medium_url") or default_photo.get("url") or "",
                    "atribuicao": default_photo.get("attribution") or "",
                    "licenca": default_photo.get("license_code") or "",
                })

            result = {
                "sucesso": True,
                "erro": None,
                "taxon_id": taxon_id,
                "nome_cientifico": taxon.get("name") or "",
                "nome_popular": taxon.get("preferred_common_name") or "",
                "rank": taxon.get("rank") or "",
                "ocorrencias_total": obs_count,
                "fenologia": fenologia,
                "imagens": images[:5],
                "wikipedia_url": taxon.get("wikipedia_url") or "",
            }
            cache.set(cache_key, result, CACHE_TTL)
            return result

        except requests.RequestException as exc:
            logger.warning("iNaturalist indisponível: %s", exc)
            return {"sucesso": False, "erro": f"Erro de rede: {exc}", "nome_submetido": nome_cientifico}

    def _search_taxon(self, nome: str) -> dict | None:
        url = f"{INATURALIST_API_BASE}/taxa"
        response = self.session.get(
            url, params={"q": nome, "rank": "species", "per_page": 1},
            timeout=self.timeout, headers={"User-Agent": self.user_agent},
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        return results[0] if results else None

    def _observation_count(self, taxon_id: int) -> int:
        url = f"{INATURALIST_API_BASE}/observations"
        try:
            response = self.session.get(
                url, params={"taxon_id": taxon_id, "per_page": 0},
                timeout=self.timeout, headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            return response.json().get("total_results", 0)
        except requests.RequestException:
            return 0

    def _compute_phenology(self, taxon_id: int) -> dict:
        """Analisa distribuição mensal das observações para fenologia."""
        url = f"{INATURALIST_API_BASE}/observations"
        try:
            response = self.session.get(
                url, params={
                    "taxon_id": taxon_id,
                    "per_page": 200,
                    "order_by": "observed_on",
                    "quality_grade": "research",
                    "fields": "observed_on",
                },
                timeout=self.timeout, headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            results = response.json().get("results") or []

            month_counter = Counter()
            for obs in results:
                observed_on = obs.get("observed_on") or ""
                if len(observed_on) >= 7:
                    try:
                        month = int(observed_on[5:7])
                        month_counter[month] += 1
                    except (ValueError, IndexError):
                        pass

            meses_nomes = {
                1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
            }

            meses = {meses_nomes.get(m, str(m)): c for m, c in sorted(month_counter.items())}

            estacao_pico = ""
            if month_counter:
                pico_mes = month_counter.most_common(1)[0][0]
                estacao_pico = meses_nomes.get(pico_mes, "")

            return {"meses": meses, "estacao_pico": estacao_pico}

        except requests.RequestException:
            return {"meses": {}, "estacao_pico": ""}

    def _observation_photos(self, taxon_id: int) -> list[dict]:
        url = f"{INATURALIST_API_BASE}/observations"
        try:
            response = self.session.get(
                url, params={
                    "taxon_id": taxon_id,
                    "per_page": 5,
                    "photos": "true",
                    "quality_grade": "research",
                    "order_by": "votes",
                },
                timeout=self.timeout, headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            results = response.json().get("results") or []
            images = []
            for obs in results:
                photos = obs.get("photos") or []
                for photo in photos[:1]:
                    url_img = photo.get("url") or ""
                    if url_img:
                        # Converter thumbnail para medium
                        url_img = url_img.replace("square", "medium")
                        images.append({
                            "url": url_img,
                            "atribuicao": photo.get("attribution") or "",
                            "licenca": photo.get("license_code") or "",
                        })
            return images
        except requests.RequestException:
            return []
