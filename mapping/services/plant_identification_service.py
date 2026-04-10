import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import requests
from django.core.cache import cache
from django.db.models import Q
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mapping.models import PlantaReferencial
from mapping.utils.cache_keys import build_safe_cache_key

logger = logging.getLogger(__name__)


@dataclass
class IdentificationResult:
    nome_popular: str = ""
    nome_cientifico: str = ""
    score: float = 0.0
    fonte: str = "local"
    status_identificacao: str = "pendente"
    candidatos: list[dict[str, Any]] | None = None
    taxonomia: dict[str, Any] | None = None


@contextmanager
def _open_image_file(foto):
    if not foto:
        yield None
        return

    if hasattr(foto, "read"):
        try:
            foto.seek(0)
        except Exception:
            logger.debug("Não foi possível resetar o cursor da imagem.")
        yield foto
        return

    with open(foto, "rb") as arquivo:
        yield arquivo


class PlantIdentificationService:
    def __init__(self):
        retry_kwargs = {
            "total": 2,
            "read": 2,
            "connect": 2,
            "status_forcelist": [429, 500, 502, 503, 504],
            "backoff_factor": 0.3,
        }
        try:
            retry = Retry(allowed_methods=["GET", "POST"], **retry_kwargs)
        except TypeError:
            # Compatibilidade com urllib3 antigo (<1.26), usado em alguns ambientes.
            retry = Retry(method_whitelist=["GET", "POST"], **retry_kwargs)
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.timeout = float(os.environ.get("PLANT_API_TIMEOUT", "12"))
        self.user_agent = os.environ.get(
            "COLABORAPANC_HTTP_USER_AGENT",
            "ColaboraPANC/1.0 (+https://foodlens.com.br)",
        )

    def identify(self, *, foto=None, nome_popular: str = "", nome_cientifico: str = "", lat=None, lon=None) -> IdentificationResult:
        candidatos: list[dict[str, Any]] = []

        if foto:
            plantnet = self._identify_with_plantnet(foto)
            if plantnet:
                candidatos.append(plantnet)

        nome_base = (
            candidatos[0].get("nome_cientifico")
            if candidatos and candidatos[0].get("nome_cientifico")
            else nome_cientifico or nome_popular
        )

        inat = self._identify_with_inaturalist(
            query=nome_base,
            lat=lat,
            lon=lon,
            with_photo=bool(foto),
        )
        if inat:
            candidatos.append(inat)

        local = self._identify_locally(nome_popular=nome_popular, nome_cientifico=nome_cientifico)
        if local:
            candidatos.append(local)

        melhor = self._pick_best_candidate(candidatos)
        taxonomia = None
        if melhor.get("nome_cientifico"):
            taxonomia = self._normalize_with_gbif(melhor["nome_cientifico"])
            if taxonomia.get("nome_cientifico_valido"):
                melhor["nome_cientifico"] = taxonomia["nome_cientifico_valido"]

        return IdentificationResult(
            nome_popular=melhor.get("nome_popular", ""),
            nome_cientifico=melhor.get("nome_cientifico", ""),
            score=float(melhor.get("score", 0.0) or 0.0),
            fonte=melhor.get("fonte", "local"),
            status_identificacao="sugerido" if (melhor.get("nome_popular") or melhor.get("nome_cientifico")) else "pendente",
            candidatos=candidatos,
            taxonomia=taxonomia or {},
        )

    def resolve_or_create_planta(self, *, nome_popular: str = "", nome_cientifico: str = "", identification: IdentificationResult | None = None) -> tuple[PlantaReferencial | None, str]:
        pop = (nome_popular or (identification.nome_popular if identification else "") or "").strip()
        sci = (nome_cientifico or (identification.nome_cientifico if identification else "") or "").strip()

        if sci:
            planta = PlantaReferencial.objects.filter(
                Q(nome_cientifico__iexact=sci)
                | Q(nome_cientifico_valido__iexact=sci)
                | Q(nome_cientifico_corrigido__iexact=sci)
            ).first()
            if planta:
                self._update_taxonomy_fields(planta, identification)
                return planta, "planta existente por nome científico"

        if pop:
            planta = PlantaReferencial.objects.filter(nome_popular__iexact=pop).first()
            if planta:
                if sci and not planta.nome_cientifico:
                    planta.nome_cientifico = sci
                self._update_taxonomy_fields(planta, identification)
                planta.save(update_fields=[
                    "nome_cientifico",
                    "nome_cientifico_valido",
                    "nome_cientifico_corrigido",
                    "fonte_validacao",
                ])
                return planta, "planta existente por nome popular"

        if not pop and not sci:
            return None, "Não foi possível identificar a planta com segurança. Informe nome popular/científico ou tente outra foto."

        planta = PlantaReferencial.objects.create(
            nome_popular=pop or sci.title(),
            nome_cientifico=sci,
            nome_cientifico_valido=(identification.taxonomia or {}).get("nome_cientifico_valido", "") if identification else "",
            nome_cientifico_corrigido=(identification.taxonomia or {}).get("nome_cientifico_corrigido", "") if identification else "",
            fonte_validacao=(identification.taxonomia or {}).get("fonte", "") if identification else "",
        )
        return planta, "planta criada automaticamente"

    def _update_taxonomy_fields(self, planta: PlantaReferencial, identification: IdentificationResult | None) -> None:
        if not identification or not identification.taxonomia:
            return
        tax = identification.taxonomia
        if tax.get("nome_cientifico_valido"):
            planta.nome_cientifico_valido = tax["nome_cientifico_valido"]
        if tax.get("nome_cientifico_corrigido"):
            planta.nome_cientifico_corrigido = tax["nome_cientifico_corrigido"]
        if tax.get("fonte"):
            planta.fonte_validacao = tax["fonte"]

    def _identify_locally(self, *, nome_popular: str, nome_cientifico: str) -> dict[str, Any]:
        if not nome_popular and not nome_cientifico:
            return {}

        q = Q()
        if nome_popular:
            q |= Q(nome_popular__icontains=nome_popular)
        if nome_cientifico:
            q |= Q(nome_cientifico__icontains=nome_cientifico)
            q |= Q(nome_cientifico_valido__icontains=nome_cientifico)

        planta = PlantaReferencial.objects.filter(q).first()
        if not planta:
            return {}

        return {
            "fonte": "base_local",
            "nome_popular": planta.nome_popular or nome_popular,
            "nome_cientifico": planta.nome_cientifico or planta.nome_cientifico_valido or nome_cientifico,
            "score": 0.9,
        }

    def _identify_with_plantnet(self, foto) -> dict[str, Any]:
        api_key = os.environ.get("PLANTNET_API_KEY", "").strip()
        if not api_key:
            return {}

        url = f"{os.environ.get('PLANTNET_API_URL', 'https://my-api.plantnet.org/v2/identify/all')}"

        try:
            with _open_image_file(foto) as arquivo:
                if not arquivo:
                    return {}
                response = self.session.post(
                    url,
                    params={"api-key": api_key},
                    data={"organs": "leaf"},
                    files={"images": arquivo},
                    timeout=self.timeout,
                    headers={"User-Agent": self.user_agent},
                )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results") or []
            if not results:
                return {}
            best = results[0]
            species = best.get("species") or {}
            common_names = species.get("commonNames") or []
            return {
                "fonte": "PlantNet",
                "nome_popular": common_names[0] if common_names else "",
                "nome_cientifico": species.get("scientificNameWithoutAuthor", ""),
                "score": float(best.get("score", 0.0) or 0.0),
                "raw": best,
            }
        except requests.RequestException as exc:
            logger.warning("PlantNet indisponível: %s", exc)
            return {}

    def _identify_with_inaturalist(self, *, query: str = "", lat=None, lon=None, with_photo: bool = False) -> dict[str, Any]:
        cache_key = build_safe_cache_key("inat-identify", query, lat, lon, with_photo)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        url = os.environ.get("INATURALIST_API_URL", "https://api.inaturalist.org/v1/observations")
        params = {
            "per_page": 1,
            "order_by": "votes",
            "photos": "true" if with_photo else None,
            "q": query or None,
            "lat": lat,
            "lng": lon,
            "radius": 25 if lat and lon else None,
        }
        params = {k: v for k, v in params.items() if v not in (None, "")}

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results") or []
            if not results:
                cache.set(cache_key, {}, 60 * 20)
                return {}

            taxon = (results[0] or {}).get("taxon") or {}
            names = taxon.get("preferred_common_name") or ""
            scientific = taxon.get("name") or ""
            score = 0.75
            result = {
                "fonte": "iNaturalist",
                "nome_popular": names,
                "nome_cientifico": scientific,
                "score": score,
                "raw": taxon,
            }
            cache.set(cache_key, result, 60 * 20)
            return result
        except requests.RequestException as exc:
            logger.warning("iNaturalist indisponível: %s", exc)
            return {}

    def _normalize_with_gbif(self, nome_cientifico: str) -> dict[str, Any]:
        nome_cientifico = (nome_cientifico or "").strip()
        if not nome_cientifico:
            return {}

        cache_key = build_safe_cache_key("gbif-match", nome_cientifico)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        url = os.environ.get("GBIF_MATCH_API_URL", "https://api.gbif.org/v1/species/match")

        try:
            response = self.session.get(
                url,
                params={"name": nome_cientifico},
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            payload = response.json()
            valid_name = payload.get("scientificName") or ""
            result = {
                "nome_cientifico_corrigido": nome_cientifico,
                "nome_cientifico_valido": valid_name,
                "fonte": "GBIF",
                "status": payload.get("matchType", "NONE"),
            }
            cache.set(cache_key, result, 60 * 60 * 6)
            return result
        except requests.RequestException as exc:
            logger.warning("GBIF indisponível: %s", exc)
            return {}

    @staticmethod
    def _pick_best_candidate(candidatos: list[dict[str, Any]]) -> dict[str, Any]:
        if not candidatos:
            return {}
        return sorted(candidatos, key=lambda x: float(x.get("score", 0.0) or 0.0), reverse=True)[0]
