"""
Serviço de integração com Global Names Verifier API.
Documentação: https://apidoc.globalnames.org/gnames
Endpoint: https://verifier.globalnames.org/api/v1/verifications
"""

import logging
import os

import requests
from django.core.cache import cache
from mapping.utils.cache_keys import build_safe_cache_key

logger = logging.getLogger(__name__)

GLOBALNAMES_API_URL = "https://verifier.globalnames.org/api/v1/verifications"
CACHE_TTL = 60 * 60 * 12  # 12 horas


class GlobalNamesService:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.timeout = float(os.environ.get("ENRICHMENT_API_TIMEOUT", "15"))
        self.user_agent = os.environ.get(
            "COLABORAPANC_HTTP_USER_AGENT",
            "ColaboraPANC/1.0 (+https://foodlens.com.br)",
        )

    def verify(self, nome_cientifico: str) -> dict:
        """
        Verifica um nome científico no Global Names Verifier.

        Retorna dict com:
        - nome_submetido: str
        - nome_validado: str
        - match_type: str (Exact, Fuzzy, PartialExact, etc.)
        - data_source_title: str (fonte primária usada)
        - data_source_id: int
        - classification_path: str
        - score: float (0-1)
        - sinonimos: list[str]
        - autoria: str
        - sucesso: bool
        - erro: str | None
        """
        nome_cientifico = (nome_cientifico or "").strip()
        if not nome_cientifico:
            return {"sucesso": False, "erro": "Nome científico vazio"}

        cache_key = build_safe_cache_key("gnames", nome_cientifico)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = self.session.post(
                GLOBALNAMES_API_URL,
                json={"nameStrings": [nome_cientifico]},
                timeout=self.timeout,
                headers={
                    "User-Agent": self.user_agent,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            payload = response.json()

            names = payload.get("names") or []
            if not names:
                result = {
                    "sucesso": False,
                    "erro": "Nenhum resultado encontrado",
                    "nome_submetido": nome_cientifico,
                }
                cache.set(cache_key, result, 60 * 30)
                return result

            name_entry = names[0]
            best_result = name_entry.get("bestResult") or {}

            # Extrair sinônimos de results adicionais
            all_results = name_entry.get("results") or []
            sinonimos = []
            for r in all_results:
                current_name = r.get("currentCanonicalSimple") or ""
                matched_name = r.get("matchedCanonicalSimple") or ""
                for n in [current_name, matched_name]:
                    if n and n.lower() != nome_cientifico.lower() and n not in sinonimos:
                        sinonimos.append(n)

            result = {
                "sucesso": True,
                "erro": None,
                "nome_submetido": nome_cientifico,
                "nome_validado": best_result.get("currentCanonicalSimple") or best_result.get("matchedCanonicalSimple") or "",
                "nome_com_autoria": best_result.get("currentName") or "",
                "autoria": _extract_authorship(
                    best_result.get("currentName") or "",
                    best_result.get("currentCanonicalSimple") or "",
                ),
                "match_type": best_result.get("matchType") or "",
                "data_source_title": best_result.get("dataSourceTitleShort") or "",
                "data_source_id": best_result.get("dataSourceId"),
                "classification_path": best_result.get("classificationPath") or "",
                "score": _compute_gn_score(best_result),
                "sinonimos": sinonimos[:20],
            }
            cache.set(cache_key, result, CACHE_TTL)
            return result

        except requests.RequestException as exc:
            logger.warning("Global Names Verifier indisponível: %s", exc)
            return {
                "sucesso": False,
                "erro": f"Erro de rede: {exc}",
                "nome_submetido": nome_cientifico,
            }


def _extract_authorship(full_name: str, canonical: str) -> str:
    """Extrai a autoria subtraindo o nome canônico do nome completo."""
    if not full_name or not canonical:
        return ""
    if canonical in full_name:
        authorship = full_name.replace(canonical, "").strip()
        return authorship.strip("() ")
    return ""


def _compute_gn_score(best_result: dict) -> float:
    """Calcula score de confiança baseado no tipo de match."""
    match_type = (best_result.get("matchType") or "").lower()
    scores = {
        "exact": 1.0,
        "partialexact": 0.85,
        "fuzzy": 0.6,
        "partialfuzzy": 0.4,
    }
    return scores.get(match_type, 0.3)
