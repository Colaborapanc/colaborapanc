"""
Serviço de integração com Tropicos API.
Documentação: http://services.tropicos.org/help
"""

import logging
import os

import requests
from django.core.cache import cache
from mapping.utils.cache_keys import build_safe_cache_key

logger = logging.getLogger(__name__)

TROPICOS_BASE_URL = "http://services.tropicos.org"
CACHE_TTL = 60 * 60 * 24  # 24 horas


class TropicosService:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.api_key = os.environ.get("TROPICOS_API_KEY", "dc34a4c3-1bf2-4edf-9488-b11e9f860744")
        self.timeout = float(os.environ.get("ENRICHMENT_API_TIMEOUT", "15"))
        self.user_agent = os.environ.get(
            "COLABORAPANC_HTTP_USER_AGENT",
            "ColaboraPANC/1.0 (+https://foodlens.com.br)",
        )

    def search_name(self, nome_cientifico: str) -> dict:
        """
        Busca um nome científico no Tropicos.
        Retorna dict com:
        - name_id: int
        - nome_cientifico: str
        - autoria: str
        - familia: str
        - nome_aceito: str
        - nome_aceito_id: int
        - sinonimos: list[dict]
        - distribuicao: str
        - imagens: list[dict]
        - sucesso: bool
        - erro: str | None
        """
        nome_cientifico = (nome_cientifico or "").strip()
        if not nome_cientifico:
            return {"sucesso": False, "erro": "Nome científico vazio"}

        cache_key = build_safe_cache_key("tropicos", nome_cientifico)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            # 1. Buscar nome
            search_result = self._search(nome_cientifico)
            if not search_result:
                result = {"sucesso": False, "erro": "Nome não encontrado no Tropicos", "nome_submetido": nome_cientifico}
                cache.set(cache_key, result, 60 * 60)
                return result

            name_id = search_result.get("NameId")
            if not name_id:
                result = {"sucesso": False, "erro": "NameId ausente no Tropicos", "nome_submetido": nome_cientifico}
                cache.set(cache_key, result, 60 * 60)
                return result

            # 2. Detalhes do nome
            details = self._get_name_details(name_id)

            # 3. Nomes aceitos
            accepted = self._get_accepted_names(name_id)

            # 4. Sinônimos
            synonyms = self._get_synonyms(name_id)

            # 5. Imagens
            images = self._get_images(name_id)

            nome_aceito = ""
            nome_aceito_id = None
            if accepted:
                first_accepted = accepted[0]
                accepted_name_info = first_accepted.get("AcceptedName") or {}
                nome_aceito = accepted_name_info.get("ScientificName") or ""
                nome_aceito_id = accepted_name_info.get("NameId")

            sinonimos_lista = []
            for syn in synonyms:
                syn_name = syn.get("SynonymName") or {}
                s = syn_name.get("ScientificName") or ""
                if s and s.lower() != nome_cientifico.lower():
                    sinonimos_lista.append({
                        "nome": s,
                        "name_id": syn_name.get("NameId"),
                        "autoria": syn_name.get("Author") or "",
                    })

            imagens_lista = []
            for img in images[:5]:
                detail_url = img.get("DetailUrl") or img.get("ImageUrl") or ""
                thumbnail = img.get("ThumbnailUrl") or detail_url
                if detail_url:
                    imagens_lista.append({
                        "url": detail_url,
                        "thumbnail": thumbnail,
                        "caption": img.get("Caption") or "",
                        "copyright": img.get("Copyright") or "",
                    })

            result = {
                "sucesso": True,
                "erro": None,
                "name_id": name_id,
                "nome_cientifico": details.get("ScientificName") or search_result.get("ScientificName") or "",
                "autoria": details.get("Author") or search_result.get("Author") or "",
                "familia": details.get("Family") or "",
                "nome_aceito": nome_aceito,
                "nome_aceito_id": nome_aceito_id,
                "sinonimos": sinonimos_lista[:20],
                "distribuicao": details.get("NomenclatureStatusName") or "",
                "imagens": imagens_lista,
            }
            cache.set(cache_key, result, CACHE_TTL)
            return result

        except requests.RequestException as exc:
            logger.warning("Tropicos indisponível: %s", exc)
            return {"sucesso": False, "erro": f"Erro de rede: {exc}", "nome_submetido": nome_cientifico}

    def _search(self, nome: str) -> dict | None:
        url = f"{TROPICOS_BASE_URL}/Name/Search"
        params = {
            "name": nome,
            "type": "wildcard",
            "apikey": self.api_key,
            "format": "json",
        }
        response = self.session.get(url, params=params, timeout=self.timeout, headers={"User-Agent": self.user_agent})
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            # Filtrar erros Tropicos (retorna lista com erro)
            first = data[0]
            if "Error" in first:
                return None
            return first
        return None

    def _get_name_details(self, name_id: int) -> dict:
        url = f"{TROPICOS_BASE_URL}/Name/{name_id}"
        params = {"apikey": self.api_key, "format": "json"}
        response = self.session.get(url, params=params, timeout=self.timeout, headers={"User-Agent": self.user_agent})
        response.raise_for_status()
        return response.json() or {}

    def _get_accepted_names(self, name_id: int) -> list:
        url = f"{TROPICOS_BASE_URL}/Name/{name_id}/AcceptedNames"
        params = {"apikey": self.api_key, "format": "json"}
        try:
            response = self.session.get(url, params=params, timeout=self.timeout, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data and "Error" not in data[0]:
                return data
        except requests.RequestException:
            pass
        return []

    def _get_synonyms(self, name_id: int) -> list:
        url = f"{TROPICOS_BASE_URL}/Name/{name_id}/Synonyms"
        params = {"apikey": self.api_key, "format": "json"}
        try:
            response = self.session.get(url, params=params, timeout=self.timeout, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data and "Error" not in data[0]:
                return data
        except requests.RequestException:
            pass
        return []

    def _get_images(self, name_id: int) -> list:
        url = f"{TROPICOS_BASE_URL}/Name/{name_id}/Images"
        params = {"apikey": self.api_key, "format": "json"}
        try:
            response = self.session.get(url, params=params, timeout=self.timeout, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data and "Error" not in data[0]:
                return data
        except requests.RequestException:
            pass
        return []
