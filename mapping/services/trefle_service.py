"""
Serviço de integração com Trefle API (OPCIONAL, baixa prioridade).
Documentação: https://docs.trefle.io/reference
Nunca usar como verdade científica final - apenas para sugestão de dados extras.
"""

import logging
import os

import requests
from django.core.cache import cache
from mapping.utils.cache_keys import build_safe_cache_key

logger = logging.getLogger(__name__)

TREFLE_API_BASE = "https://trefle.io/api/v1"
CACHE_TTL = 60 * 60 * 24  # 24 horas


class TrefleService:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.token = os.environ.get("TREFLE_API_TOKEN", "usr-V8E4TFez3OflTjXOHHV3hltc2J4231KmVysctucAGD4")
        self.timeout = float(os.environ.get("ENRICHMENT_API_TIMEOUT", "15"))
        self.user_agent = os.environ.get(
            "COLABORAPANC_HTTP_USER_AGENT",
            "ColaboraPANC/1.0 (+https://foodlens.com.br)",
        )

    def enrich(self, nome_cientifico: str) -> dict:
        """
        Busca dados extras no Trefle (comestibilidade, ciclo de vida, etc.).
        NUNCA usar como confirmação taxonômica - apenas sugestão.

        Retorna dict com:
        - trefle_id: int
        - nome_cientifico: str
        - nome_popular: str
        - comestivel: bool | None
        - partes_comestiveis: list[str]
        - ciclo_vida: str
        - crescimento_habito: str
        - imagem_url: str
        - sucesso: bool
        - erro: str | None
        - aviso: str (sempre inclui aviso sobre baixa prioridade)
        """
        nome_cientifico = (nome_cientifico or "").strip()
        if not nome_cientifico:
            return {"sucesso": False, "erro": "Nome científico vazio"}

        if not self.token:
            return {"sucesso": False, "erro": "Token Trefle não configurado"}

        cache_key = build_safe_cache_key("trefle", nome_cientifico)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            # Busca por nome científico
            url = f"{TREFLE_API_BASE}/plants/search"
            response = self.session.get(
                url,
                params={"q": nome_cientifico, "token": self.token},
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            data = response.json().get("data") or []

            if not data:
                result = {
                    "sucesso": False,
                    "erro": "Planta não encontrada no Trefle",
                    "nome_submetido": nome_cientifico,
                    "aviso": "Trefle é fonte opcional - dados não confirmados cientificamente.",
                }
                cache.set(cache_key, result, 60 * 60 * 6)
                return result

            plant = data[0]
            plant_id = plant.get("id")

            # Buscar detalhes completos
            detail = self._get_plant_detail(plant_id) if plant_id else {}

            edible_parts = []
            edible = None
            if detail:
                specifications = detail.get("specifications") or {}
                growth = detail.get("growth") or {}
                edible_part = detail.get("edible_part") or []
                edible = detail.get("edible")
                edible_parts = edible_part if isinstance(edible_part, list) else []

            result = {
                "sucesso": True,
                "erro": None,
                "aviso": "Trefle é fonte opcional de baixa prioridade - nunca usar como verdade científica final.",
                "trefle_id": plant_id,
                "nome_cientifico": plant.get("scientific_name") or "",
                "nome_popular": plant.get("common_name") or "",
                "familia": plant.get("family") or "",
                "genero": plant.get("genus") or "",
                "comestivel": edible,
                "partes_comestiveis": edible_parts,
                "ciclo_vida": (detail.get("specifications") or {}).get("growth_habit") or "",
                "crescimento_habito": (detail.get("specifications") or {}).get("growth_form") or "",
                "imagem_url": plant.get("image_url") or "",
            }
            cache.set(cache_key, result, CACHE_TTL)
            return result

        except requests.RequestException as exc:
            logger.warning("Trefle indisponível: %s", exc)
            return {
                "sucesso": False,
                "erro": f"Erro de rede: {exc}",
                "nome_submetido": nome_cientifico,
                "aviso": "Trefle é fonte opcional - falha não afeta enriquecimento principal.",
            }

    def _get_plant_detail(self, plant_id: int) -> dict:
        url = f"{TREFLE_API_BASE}/plants/{plant_id}"
        try:
            response = self.session.get(
                url,
                params={"token": self.token},
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            return response.json().get("data") or {}
        except requests.RequestException:
            return {}
